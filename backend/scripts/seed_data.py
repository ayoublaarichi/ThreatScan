"""
Seed the database with sample data for development and demos.

Usage:
    cd backend
    python -m scripts.seed_data
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings
from app.database import Base
from app.models.file import File
from app.models.scan_job import ScanJob
from app.models.report import Report
from app.models.indicator import Indicator
from app.models.file_indicator import FileIndicator
from app.models.yara_match import YaraMatch
from app.models.extracted_string import ExtractedString
from app.models.comment import Comment
from app.models.tag import Tag, FileTag


SAMPLE_FILES = [
    {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
        "file_name": "dropper_v2.exe",
        "file_size": 245760,
        "mime_type": "application/x-dosexec",
        "magic_description": "PE32 executable (GUI) Intel 80386, for MS Windows",
        "entropy": 7.234,
        "score": 75,
        "verdict": "malicious",
    },
    {
        "sha256": "a" * 64,
        "sha1": "b" * 40,
        "md5": "c" * 32,
        "file_name": "invoice_macro.docm",
        "file_size": 98304,
        "mime_type": "application/vnd.ms-word.document.macroEnabled.12",
        "magic_description": "Microsoft Word 2007+",
        "entropy": 5.812,
        "score": 55,
        "verdict": "suspicious",
    },
    {
        "sha256": "1" * 64,
        "sha1": "2" * 40,
        "md5": "3" * 32,
        "file_name": "clean_utility.exe",
        "file_size": 51200,
        "mime_type": "application/x-dosexec",
        "magic_description": "PE32 executable (console) Intel 80386, for MS Windows",
        "entropy": 4.123,
        "score": 5,
        "verdict": "clean",
    },
]

SAMPLE_INDICATORS = [
    {"indicator_type": "domain", "value": "malware-c2.example.com", "reputation": "malicious"},
    {"indicator_type": "ip", "value": "185.123.45.67", "reputation": "suspicious"},
    {"indicator_type": "url", "value": "https://malware-c2.example.com/payload.bin", "reputation": "malicious"},
    {"indicator_type": "email", "value": "attacker@evil-domain.com", "reputation": "malicious"},
    {"indicator_type": "domain", "value": "cdn-update.example.net", "reputation": "suspicious"},
    {"indicator_type": "ip", "value": "203.0.113.42", "reputation": "suspicious"},
]

SAMPLE_TAGS = [
    {"name": "trojan", "color": "#ef4444"},
    {"name": "dropper", "color": "#f97316"},
    {"name": "macro", "color": "#eab308"},
    {"name": "ransomware", "color": "#dc2626"},
    {"name": "clean", "color": "#22c55e"},
    {"name": "packed", "color": "#8b5cf6"},
]


async def seed():
    """Insert sample data into the database."""
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        async with session.begin():
            now = datetime.now(timezone.utc)

            # ── Tags ──
            tags = {}
            for t in SAMPLE_TAGS:
                tag = Tag(**t)
                session.add(tag)
                tags[t["name"]] = tag
            await session.flush()

            # ── Indicators ──
            indicators = {}
            for ind_data in SAMPLE_INDICATORS:
                ind = Indicator(**ind_data)
                session.add(ind)
                indicators[ind_data["value"]] = ind
            await session.flush()

            # ── Files, Jobs, Reports ──
            for i, fd in enumerate(SAMPLE_FILES):
                score = fd.pop("score")
                verdict = fd.pop("verdict")

                file = File(**fd)
                file.first_seen = now - timedelta(days=10 - i)
                file.last_seen = now - timedelta(days=i)
                session.add(file)
                await session.flush()

                # Scan job
                job = ScanJob(
                    file_id=file.id,
                    status="completed",
                    stage="done",
                    progress=100,
                )
                session.add(job)

                # Report
                report = Report(
                    file_id=file.id,
                    score=score,
                    verdict=verdict,
                    summary=f"Sample analysis: {verdict} with score {score}/100",
                    pe_info={"machine": "0x14c", "sections": []} if "exe" in fd["file_name"] else None,
                    scoring_details={"yara_rules": [], "ioc_hits": []},
                    analysis_duration_ms=2500 + i * 500,
                )
                session.add(report)

                # Link first file to indicators
                if i == 0:
                    for ind in list(indicators.values())[:3]:
                        fi = FileIndicator(file_id=file.id, indicator_id=ind.id)
                        session.add(fi)

                    # YARA match
                    ym = YaraMatch(
                        file_id=file.id,
                        rule_name="Suspicious_Process_Injection",
                        rule_namespace="malware_core",
                        rule_tags=["critical"],
                        severity="critical",
                        description="Detects process injection API patterns",
                        matched_strings=[{"offset": 4520, "identifier": "$api1"}],
                        score_contribution=30,
                    )
                    session.add(ym)

                    # Tag
                    ft = FileTag(file_id=file.id, tag_id=tags["trojan"].id)
                    session.add(ft)
                    ft2 = FileTag(file_id=file.id, tag_id=tags["dropper"].id)
                    session.add(ft2)

                    # Comment
                    comment = Comment(
                        file_id=file.id,
                        content="This sample was found in a phishing campaign targeting the finance sector.",
                        author_name="analyst1",
                    )
                    session.add(comment)

                # Second file gets macro tag
                if i == 1:
                    ft = FileTag(file_id=file.id, tag_id=tags["macro"].id)
                    session.add(ft)
                    fi = FileIndicator(file_id=file.id, indicator_id=indicators["cdn-update.example.net"].id)
                    session.add(fi)

                # Third file gets clean tag
                if i == 2:
                    ft = FileTag(file_id=file.id, tag_id=tags["clean"].id)
                    session.add(ft)

                # Extracted strings for each file
                for j, s in enumerate(["MZ", "This program cannot be run", "kernel32.dll", "VirtualAlloc"]):
                    es = ExtractedString(
                        file_id=file.id,
                        value=s,
                        encoding="ascii",
                        category="generic" if j < 2 else "import",
                        offset=j * 100,
                    )
                    session.add(es)

    await engine.dispose()
    print("✓ Database seeded with sample data.")
    print(f"  → {len(SAMPLE_FILES)} files")
    print(f"  → {len(SAMPLE_INDICATORS)} indicators")
    print(f"  → {len(SAMPLE_TAGS)} tags")


if __name__ == "__main__":
    asyncio.run(seed())
