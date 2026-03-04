"""
ThreatScan — Celery tasks (analysis pipeline).

The main analysis pipeline runs as a series of stages.
Each stage updates the job status and persists results to the database.
"""

import time
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging import get_logger
from app.worker.celery_app import celery_app

logger = get_logger(__name__)
settings = get_settings()


def _get_sync_session() -> Session:
    """Create a synchronous database session for Celery workers."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _update_job(session: Session, job_id: str, **kwargs) -> None:
    """Update a scan job's status fields."""
    from app.models.scan_job import ScanJob

    job = session.execute(
        select(ScanJob).where(ScanJob.id == job_id)
    ).scalar_one_or_none()

    if job:
        for key, value in kwargs.items():
            setattr(job, key, value)
        session.commit()


@celery_app.task(
    name="app.worker.tasks.run_analysis_pipeline",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def run_analysis_pipeline(self, job_id: str, file_id: str, sha256: str) -> dict:
    """
    Main analysis pipeline — processes a file through all analysis stages.

    Stages:
        1. File ingestion — download from storage
        2. Hash computation — SHA256, MD5, SHA1
        3. File metadata — mime type, entropy, size
        4. String extraction — ASCII/UTF-16 strings
        5. IOC extraction — domains, URLs, IPs, emails
        6. YARA scanning — rule matching
        7. Scoring & verdict — threat score generation
        8. Report creation — persist final report

    Args:
        job_id: UUID of the scan job
        file_id: UUID of the file record
        sha256: SHA256 hash of the file
    """
    from app.models.extracted_string import ExtractedString
    from app.models.file import File as FileModel
    from app.models.file_indicator import FileIndicator
    from app.models.indicator import Indicator
    from app.models.report import Report
    from app.models.scan_job import ScanJob
    from app.models.yara_match import YaraMatch
    from app.services.storage import StorageService
    from app.worker.analysis import (
        analyze_pe,
        compute_entropy,
        compute_score,
        extract_iocs,
        extract_strings,
        scan_yara,
    )

    session = _get_sync_session()
    storage = StorageService()
    start_time = time.time()

    try:
        # ── Stage 1: File Ingestion ──
        logger.info("Stage 1: File ingestion", job_id=job_id, sha256=sha256)
        _update_job(
            session, job_id,
            status="processing",
            current_stage="ingestion",
            progress=5,
            started_at=datetime.now(timezone.utc),
        )

        # Get file record
        file_record = session.execute(
            select(FileModel).where(FileModel.id == file_id)
        ).scalar_one_or_none()

        if not file_record:
            raise ValueError(f"File record not found: {file_id}")

        # Download from storage
        storage_path = file_record.storage_path.replace(f"{storage.bucket}/", "")
        data = storage.download_file(storage_path)

        if not data:
            raise ValueError(f"Could not download file from storage: {storage_path}")

        logger.info("Stage 1 complete", size=len(data))

        # ── Stage 2: Hash Verification ──
        logger.info("Stage 2: Hash verification", job_id=job_id)
        _update_job(session, job_id, current_stage="hashing", progress=15)

        from app.services.validation import compute_hashes
        computed_sha256, computed_sha1, computed_md5 = compute_hashes(data)

        # Update hashes if missing
        if not file_record.sha1:
            file_record.sha1 = computed_sha1
        if not file_record.md5:
            file_record.md5 = computed_md5
        session.commit()

        logger.info("Stage 2 complete", sha256=computed_sha256)

        # ── Stage 3: File Metadata ──
        logger.info("Stage 3: File metadata", job_id=job_id)
        _update_job(session, job_id, current_stage="metadata", progress=25)

        entropy = compute_entropy(data)
        file_record.entropy = entropy
        session.commit()

        # PE analysis
        pe_info = analyze_pe(data)

        logger.info("Stage 3 complete", entropy=entropy, is_pe=pe_info is not None)

        # ── Stage 4: String Extraction ──
        logger.info("Stage 4: String extraction", job_id=job_id)
        _update_job(session, job_id, current_stage="strings", progress=40)

        strings = extract_strings(data, min_length=4)

        # Persist strings to database
        for s in strings[:2000]:  # Limit stored strings
            extracted = ExtractedString(
                file_id=file_record.id,
                value=s["value"][:4096],  # Truncate very long strings
                encoding=s["encoding"],
                offset=s["offset"],
                length=s["length"],
                category=s.get("category"),
            )
            session.add(extracted)
        session.commit()

        logger.info("Stage 4 complete", string_count=len(strings))

        # ── Stage 5: IOC Extraction ──
        logger.info("Stage 5: IOC extraction", job_id=job_id)
        _update_job(session, job_id, current_stage="ioc_extraction", progress=55)

        iocs = extract_iocs(strings, data)

        # Persist IOCs to database
        for ioc in iocs:
            # Get or create indicator
            existing = session.execute(
                select(Indicator).where(
                    Indicator.indicator_type == ioc["indicator_type"],
                    Indicator.value == ioc["value"],
                )
            ).scalar_one_or_none()

            if existing:
                existing.sample_count += 1
                existing.last_seen = datetime.now(timezone.utc)
                indicator = existing
            else:
                indicator = Indicator(
                    indicator_type=ioc["indicator_type"],
                    value=ioc["value"],
                    reputation="unknown",
                )
                session.add(indicator)
                session.flush()

            # Create file↔indicator link
            existing_link = session.execute(
                select(FileIndicator).where(
                    FileIndicator.file_id == file_record.id,
                    FileIndicator.indicator_id == indicator.id,
                )
            ).scalar_one_or_none()

            if not existing_link:
                link = FileIndicator(
                    file_id=file_record.id,
                    indicator_id=indicator.id,
                    context=ioc.get("context", "static_analysis"),
                )
                session.add(link)

        session.commit()
        logger.info("Stage 5 complete", ioc_count=len(iocs))

        # ── Stage 6: YARA Scanning ──
        logger.info("Stage 6: YARA scanning", job_id=job_id)
        _update_job(session, job_id, current_stage="yara_scan", progress=70)

        yara_matches = scan_yara(data, rules_path="/app/yara-rules")

        # Persist YARA matches
        for match in yara_matches:
            yara_record = YaraMatch(
                file_id=file_record.id,
                rule_name=match["rule_name"],
                rule_namespace=match.get("rule_namespace"),
                rule_tags=match.get("rule_tags"),
                severity=match.get("severity", "medium"),
                description=match.get("description"),
                matched_strings=match.get("matched_strings"),
                score_contribution=match.get("score_contribution", 0),
            )
            session.add(yara_record)
        session.commit()

        logger.info("Stage 6 complete", yara_match_count=len(yara_matches))

        # ── Stage 7: Scoring & Verdict ──
        logger.info("Stage 7: Scoring", job_id=job_id)
        _update_job(session, job_id, current_stage="scoring", progress=85)

        score, verdict, scoring_details = compute_score(
            yara_matches=yara_matches,
            iocs=iocs,
            strings=strings,
            entropy=entropy,
            pe_info=pe_info,
        )

        logger.info("Stage 7 complete", score=score, verdict=verdict)

        # ── Stage 8: Report Creation ──
        logger.info("Stage 8: Report creation", job_id=job_id)
        _update_job(session, job_id, current_stage="report_generation", progress=95)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Build summary
        summary_parts = []
        if verdict == "malicious":
            summary_parts.append(f"This file is classified as MALICIOUS with a score of {score}/100.")
        elif verdict == "suspicious":
            summary_parts.append(f"This file is classified as SUSPICIOUS with a score of {score}/100.")
        else:
            summary_parts.append(f"This file appears CLEAN with a score of {score}/100.")

        if yara_matches:
            rule_names = [m["rule_name"] for m in yara_matches]
            summary_parts.append(f"Matched {len(yara_matches)} YARA rule(s): {', '.join(rule_names)}.")

        if iocs:
            summary_parts.append(f"Found {len(iocs)} indicator(s) of compromise.")

        summary = " ".join(summary_parts)

        # Check for existing report (update instead of duplicate)
        existing_report = session.execute(
            select(Report).where(Report.file_id == file_record.id)
        ).scalar_one_or_none()

        if existing_report:
            existing_report.score = score
            existing_report.verdict = verdict
            existing_report.summary = summary
            existing_report.pe_info = pe_info
            existing_report.scoring_details = scoring_details
            existing_report.analysis_duration_ms = elapsed_ms
        else:
            report = Report(
                file_id=file_record.id,
                score=score,
                verdict=verdict,
                summary=summary,
                pe_info=pe_info,
                scoring_details=scoring_details,
                analysis_duration_ms=elapsed_ms,
            )
            session.add(report)

        session.commit()

        # ── Mark job completed ──
        _update_job(
            session, job_id,
            status="completed",
            current_stage="completed",
            progress=100,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Analysis pipeline completed",
            job_id=job_id,
            sha256=sha256,
            score=score,
            verdict=verdict,
            duration_ms=elapsed_ms,
        )

        return {
            "job_id": job_id,
            "sha256": sha256,
            "score": score,
            "verdict": verdict,
            "duration_ms": elapsed_ms,
        }

    except Exception as exc:
        logger.error(
            "Analysis pipeline failed",
            job_id=job_id,
            sha256=sha256,
            error=str(exc),
        )
        _update_job(
            session, job_id,
            status="failed",
            current_stage="error",
            error_message=str(exc),
            completed_at=datetime.now(timezone.utc),
        )
        session.close()

        # Retry on transient failures
        raise self.retry(exc=exc)

    finally:
        session.close()
