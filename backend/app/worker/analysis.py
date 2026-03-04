"""
ThreatScan — Analysis pipeline stages.

Each stage is a pure function that takes context and returns enriched context.
Stages are designed to be composable and independently testable.
"""

import math
import re
from typing import Any

from app.logging import get_logger

logger = get_logger(__name__)

# ────────────────────────────────────────────
# IOC extraction regex patterns
# ────────────────────────────────────────────

# IPv4
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)

# Domain names (simplified — avoids matching IPs)
DOMAIN_RE = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)"
    r"+(?:com|net|org|info|biz|io|co|uk|de|ru|cn|xyz|top|tk|ml|ga|cf|gq|"
    r"edu|gov|mil|int|eu|us|ca|au|in|jp|br|fr|it|nl|se|no|fi|dk|pl|cz|"
    r"online|site|club|live|tech|store|pro|pw|cc|ws|mobi|name|tv)\b",
    re.IGNORECASE,
)

# URLs
URL_RE = re.compile(
    r"https?://[^\s<>\"')\]}{,]+",
    re.IGNORECASE,
)

# Email addresses
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"
)

# Suspicious string patterns
SUSPICIOUS_PATTERNS = {
    "powershell": re.compile(r"(?:powershell|pwsh|invoke-expression|iex\s|invoke-webrequest)", re.I),
    "cmd_exec": re.compile(r"(?:cmd\.exe|command\.com|/c\s+)", re.I),
    "base64_blob": re.compile(r"[A-Za-z0-9+/]{50,}={0,2}"),
    "registry": re.compile(r"(?:HKEY_|HKLM|HKCU|HKCR)", re.I),
    "http_api": re.compile(r"(?:URLDownloadToFile|WinHttpRequest|InternetOpen|HttpSendRequest)", re.I),
    "crypto": re.compile(r"(?:CryptEncrypt|CryptDecrypt|AES|RSA|SHA256|MD5)", re.I),
    "injection": re.compile(r"(?:VirtualAlloc|WriteProcessMemory|CreateRemoteThread|NtCreateThread)", re.I),
    "persistence": re.compile(r"(?:CurrentVersion\\Run|schtasks|TaskScheduler)", re.I),
    "macro": re.compile(r"(?:AutoOpen|Auto_Open|Document_Open|Workbook_Open|Shell\(|WScript\.Shell)", re.I),
}


def compute_entropy(data: bytes) -> float:
    """
    Compute Shannon entropy of a byte sequence.

    Returns a value between 0.0 (perfectly uniform) and 8.0 (maximum entropy).
    """
    if not data:
        return 0.0

    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1

    length = len(data)
    entropy = 0.0
    for count in byte_counts:
        if count > 0:
            probability = count / length
            entropy -= probability * math.log2(probability)

    return round(entropy, 4)


def extract_strings(data: bytes, min_length: int = 4) -> list[dict[str, Any]]:
    """
    Extract printable ASCII and UTF-16LE strings from binary data.

    Args:
        data: Raw file bytes
        min_length: Minimum string length to extract

    Returns:
        List of extracted string dicts with value, encoding, offset, length, category.
    """
    strings: list[dict[str, Any]] = []

    # ASCII strings
    ascii_re = re.compile(rb"[\x20-\x7E]{%d,}" % min_length)
    for match in ascii_re.finditer(data):
        value = match.group().decode("ascii", errors="replace")
        category = _categorize_string(value)
        strings.append({
            "value": value,
            "encoding": "ascii",
            "offset": match.start(),
            "length": len(value),
            "category": category,
        })

    # UTF-16LE strings (common in PE files)
    utf16_re = re.compile(rb"(?:[\x20-\x7E]\x00){%d,}" % min_length)
    for match in utf16_re.finditer(data):
        try:
            value = match.group().decode("utf-16-le", errors="replace").rstrip("\x00")
            if len(value) >= min_length:
                category = _categorize_string(value)
                strings.append({
                    "value": value,
                    "encoding": "utf-16",
                    "offset": match.start(),
                    "length": len(value),
                    "category": category,
                })
        except (UnicodeDecodeError, ValueError):
            continue

    # Deduplicate by value, keep first occurrence
    seen = set()
    unique_strings = []
    for s in strings:
        if s["value"] not in seen:
            seen.add(s["value"])
            unique_strings.append(s)

    # Limit to prevent database bloat
    return unique_strings[:5000]


def _categorize_string(value: str) -> str:
    """Categorize a string based on pattern matching."""
    if URL_RE.search(value):
        return "url"
    if IPV4_RE.search(value):
        return "ip"
    if EMAIL_RE.search(value):
        return "email"
    if re.search(r"[A-Z]:\\|/usr/|/etc/|/tmp/", value, re.I):
        return "path"
    if re.search(r"HKEY_|HKLM|HKCU", value, re.I):
        return "registry"
    for pattern_name, pattern in SUSPICIOUS_PATTERNS.items():
        if pattern.search(value):
            return "suspicious"
    return "generic"


def extract_iocs(strings: list[dict[str, Any]], data: bytes) -> list[dict[str, Any]]:
    """
    Extract IOCs (Indicators of Compromise) from extracted strings and raw data.

    Returns:
        List of IOC dicts with indicator_type, value, and context.
    """
    iocs: list[dict[str, Any]] = []
    seen_values: set[str] = set()

    text_blob = " ".join(s["value"] for s in strings)

    # Extract IPs
    for match in IPV4_RE.finditer(text_blob):
        ip = match.group()
        # Skip private/local IPs
        if ip.startswith(("10.", "127.", "192.168.", "0.")):
            continue
        if ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31:
            continue
        if ip not in seen_values:
            seen_values.add(ip)
            iocs.append({
                "indicator_type": "ip",
                "value": ip,
                "context": "extracted_from_strings",
            })

    # Extract domains
    for match in DOMAIN_RE.finditer(text_blob):
        domain = match.group().lower()
        if domain not in seen_values:
            seen_values.add(domain)
            iocs.append({
                "indicator_type": "domain",
                "value": domain,
                "context": "extracted_from_strings",
            })

    # Extract URLs
    for match in URL_RE.finditer(text_blob):
        url = match.group().rstrip(".,;:)")
        if url not in seen_values:
            seen_values.add(url)
            iocs.append({
                "indicator_type": "url",
                "value": url,
                "context": "extracted_from_strings",
            })

    # Extract emails
    for match in EMAIL_RE.finditer(text_blob):
        email = match.group().lower()
        if email not in seen_values:
            seen_values.add(email)
            iocs.append({
                "indicator_type": "email",
                "value": email,
                "context": "extracted_from_strings",
            })

    return iocs


def scan_yara(data: bytes, rules_path: str = "/app/yara-rules") -> list[dict[str, Any]]:
    """
    Scan file data against YARA rules.

    Args:
        data: Raw file bytes
        rules_path: Path to the directory containing .yar files

    Returns:
        List of YARA match dicts.
    """
    matches: list[dict[str, Any]] = []

    try:
        import yara
        import os

        # Compile all .yar files in the rules directory
        rule_files = {}
        if os.path.isdir(rules_path):
            for fname in os.listdir(rules_path):
                if fname.endswith((".yar", ".yara")):
                    namespace = fname.rsplit(".", 1)[0]
                    rule_files[namespace] = os.path.join(rules_path, fname)

        if not rule_files:
            logger.warning("No YARA rules found", path=rules_path)
            return matches

        rules = yara.compile(filepaths=rule_files)
        yara_matches = rules.match(data=data, timeout=60)

        for match in yara_matches:
            # Determine severity from tags
            severity = "medium"
            if "critical" in match.tags:
                severity = "critical"
            elif "high" in match.tags:
                severity = "high"
            elif "low" in match.tags:
                severity = "low"

            # Determine score contribution based on severity
            score_map = {
                "critical": 30,
                "high": 25,
                "medium": 15,
                "low": 5,
            }

            matched_strings_data = []
            for offset, identifier, string_data in match.strings:
                matched_strings_data.append({
                    "offset": offset,
                    "identifier": identifier,
                    "data": string_data.hex()[:100],  # Truncate for storage
                })

            matches.append({
                "rule_name": match.rule,
                "rule_namespace": match.namespace,
                "rule_tags": list(match.tags),
                "severity": severity,
                "description": match.meta.get("description", ""),
                "matched_strings": matched_strings_data[:20],  # Limit
                "score_contribution": score_map.get(severity, 15),
            })

    except ImportError:
        logger.warning("yara-python not installed — skipping YARA scan")
    except Exception as e:
        logger.error("YARA scan error", error=str(e))

    return matches


def analyze_pe(data: bytes) -> dict[str, Any] | None:
    """
    Extract PE (Portable Executable) header information.

    Returns:
        Dict of PE info, or None if not a PE file.
    """
    try:
        import pefile

        pe = pefile.PE(data=data)
        info: dict[str, Any] = {
            "machine": hex(pe.FILE_HEADER.Machine),
            "number_of_sections": pe.FILE_HEADER.NumberOfSections,
            "timestamp": pe.FILE_HEADER.TimeDateStamp,
            "characteristics": hex(pe.FILE_HEADER.Characteristics),
            "entry_point": hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            "image_base": hex(pe.OPTIONAL_HEADER.ImageBase),
        }

        # Sections
        sections = []
        for section in pe.sections:
            sections.append({
                "name": section.Name.decode("utf-8", errors="replace").strip("\x00"),
                "virtual_size": section.Misc_VirtualSize,
                "raw_size": section.SizeOfRawData,
                "entropy": round(section.get_entropy(), 4),
                "characteristics": hex(section.Characteristics),
            })
        info["sections"] = sections

        # Imports
        imports = {}
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode("utf-8", errors="replace")
                functions = []
                for imp in entry.imports:
                    if imp.name:
                        functions.append(imp.name.decode("utf-8", errors="replace"))
                imports[dll_name] = functions
        info["imports"] = imports

        # Exports
        exports = []
        if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if exp.name:
                    exports.append(exp.name.decode("utf-8", errors="replace"))
        info["exports"] = exports

        pe.close()
        return info

    except ImportError:
        logger.warning("pefile not installed — skipping PE analysis")
        return None
    except Exception:
        # Not a PE file or parsing error — that's fine
        return None


def compute_score(
    yara_matches: list[dict],
    iocs: list[dict],
    strings: list[dict],
    entropy: float,
    pe_info: dict | None,
) -> tuple[int, str, dict]:
    """
    Compute threat score and verdict for a file.

    Scoring rules:
        +30  YARA malware rule hit (critical/high)
        +20  Malicious IOC reputation
        +15  Suspicious macro presence
        +10  Suspicious PowerShell strings
        +10  High entropy (>7.0)

    Verdict thresholds:
        0–24   clean
        25–59  suspicious
        60–100 malicious

    Returns:
        Tuple of (score, verdict, scoring_details).
    """
    score = 0
    details: dict[str, list[str]] = {
        "yara_rules": [],
        "ioc_hits": [],
        "suspicious_strings": [],
        "entropy_score": [],
        "pe_analysis": [],
    }

    # 1. YARA matches
    for match in yara_matches:
        contribution = match.get("score_contribution", 15)
        score += contribution
        details["yara_rules"].append(
            f"{match['rule_name']} ({match['severity']}) +{contribution}"
        )

    # 2. IOC count (rough heuristic)
    ioc_count = len(iocs)
    if ioc_count > 20:
        score += 20
        details["ioc_hits"].append(f"High IOC count: {ioc_count} indicators (+20)")
    elif ioc_count > 5:
        score += 10
        details["ioc_hits"].append(f"Moderate IOC count: {ioc_count} indicators (+10)")

    # 3. Suspicious strings
    suspicious_strings = [s for s in strings if s.get("category") == "suspicious"]
    has_powershell = any(
        SUSPICIOUS_PATTERNS["powershell"].search(s["value"]) for s in strings
    )
    has_macro = any(
        SUSPICIOUS_PATTERNS["macro"].search(s["value"]) for s in strings
    )
    has_injection = any(
        SUSPICIOUS_PATTERNS["injection"].search(s["value"]) for s in strings
    )

    if has_macro:
        score += 15
        details["suspicious_strings"].append("Suspicious macro indicators detected (+15)")

    if has_powershell:
        score += 10
        details["suspicious_strings"].append("PowerShell-related strings found (+10)")

    if has_injection:
        score += 15
        details["suspicious_strings"].append("Process injection API patterns found (+15)")

    # 4. Entropy
    if entropy > 7.5:
        score += 10
        details["entropy_score"].append(f"Very high entropy: {entropy:.4f} (+10)")
    elif entropy > 7.0:
        score += 5
        details["entropy_score"].append(f"High entropy: {entropy:.4f} (+5)")

    # 5. PE analysis
    if pe_info:
        # Check for suspicious section names
        if pe_info.get("sections"):
            for section in pe_info["sections"]:
                if section["entropy"] > 7.0:
                    score += 5
                    details["pe_analysis"].append(
                        f"High entropy section '{section['name']}': {section['entropy']:.4f} (+5)"
                    )
                    break  # Only count once

    # Cap score at 100
    score = min(score, 100)

    # Determine verdict
    if score >= 60:
        verdict = "malicious"
    elif score >= 25:
        verdict = "suspicious"
    else:
        verdict = "clean"

    return score, verdict, details
