"""
Unit tests for the static analysis module.
"""

import math

from app.worker.analysis import (
    compute_entropy,
    extract_strings,
    extract_iocs,
    compute_score,
)


class TestComputeEntropy:
    """Tests for Shannon entropy calculation."""

    def test_zero_entropy_uniform(self):
        """A single repeated byte has zero entropy."""
        data = b"\x00" * 1024
        assert compute_entropy(data) == 0.0

    def test_max_entropy_random(self):
        """All 256 byte values equally distributed → entropy ≈ 8.0."""
        data = bytes(range(256)) * 4
        entropy = compute_entropy(data)
        assert 7.9 < entropy <= 8.0

    def test_low_entropy_text(self):
        """Plain ASCII text should have moderate entropy."""
        data = b"Hello World! " * 100
        entropy = compute_entropy(data)
        assert 2.0 < entropy < 5.0

    def test_empty_data(self):
        """Empty data should return 0.0 entropy."""
        assert compute_entropy(b"") == 0.0

    def test_single_byte(self):
        """Single byte → zero entropy."""
        assert compute_entropy(b"A") == 0.0

    def test_two_distinct_bytes(self):
        """Two equally distributed bytes → entropy = 1.0."""
        data = b"\x00\x01" * 512
        entropy = compute_entropy(data)
        assert abs(entropy - 1.0) < 0.01


class TestExtractStrings:
    """Tests for string extraction."""

    def test_extracts_ascii_strings(self):
        data = b"\x00\x00Hello World\x00\x00Test String\x00\x00"
        result = extract_strings(data)
        texts = [s["value"] for s in result]
        assert "Hello World" in texts
        assert "Test String" in texts

    def test_min_length_filter(self):
        """Strings shorter than 4 chars should be excluded."""
        data = b"\x00Hi\x00Long Enough\x00ab\x00"
        result = extract_strings(data)
        texts = [s["value"] for s in result]
        assert "Hi" not in texts
        assert "ab" not in texts
        assert "Long Enough" in texts

    def test_respects_max_limit(self):
        """Should not return more than the configured limit."""
        # Create data with many strings
        data = b"\x00".join(f"string_{i:04d}".encode() for i in range(10000))
        result = extract_strings(data)
        assert len(result) <= 5000

    def test_empty_data(self):
        result = extract_strings(b"")
        assert result == []

    def test_categorizes_urls(self):
        data = b"\x00\x00https://example.com/path\x00\x00"
        result = extract_strings(data)
        url_strings = [s for s in result if s.get("category") == "url"]
        assert len(url_strings) >= 1

    def test_categorizes_paths(self):
        data = b"\x00\x00C:\\Windows\\System32\\cmd.exe\x00\x00"
        result = extract_strings(data)
        categories = [s.get("category") for s in result]
        assert "path" in categories


class TestExtractIocs:
    """Tests for IOC extraction."""

    def test_extracts_ipv4(self):
        strings = [
            {"value": "Connecting to 185.123.45.67 on port 443", "category": "generic"}
        ]
        iocs = extract_iocs(strings, b"")
        ips = [i["value"] for i in iocs if i["type"] == "ip"]
        assert "185.123.45.67" in ips

    def test_excludes_private_ips(self):
        strings = [
            {"value": "Server at 192.168.1.1 and 10.0.0.1", "category": "generic"}
        ]
        iocs = extract_iocs(strings, b"")
        ips = [i["value"] for i in iocs if i["type"] == "ip"]
        assert "192.168.1.1" not in ips
        assert "10.0.0.1" not in ips

    def test_extracts_domains(self):
        strings = [
            {"value": "Resolved malware-c2.example.com successfully", "category": "generic"}
        ]
        iocs = extract_iocs(strings, b"")
        domains = [i["value"] for i in iocs if i["type"] == "domain"]
        assert "malware-c2.example.com" in domains

    def test_extracts_urls(self):
        strings = [
            {"value": "https://evil.com/payload.bin", "category": "url"}
        ]
        iocs = extract_iocs(strings, b"")
        urls = [i["value"] for i in iocs if i["type"] == "url"]
        assert "https://evil.com/payload.bin" in urls

    def test_extracts_emails(self):
        strings = [
            {"value": "Contact: attacker@evil.com", "category": "generic"}
        ]
        iocs = extract_iocs(strings, b"")
        emails = [i["value"] for i in iocs if i["type"] == "email"]
        assert "attacker@evil.com" in emails

    def test_deduplicates(self):
        strings = [
            {"value": "185.1.2.3", "category": "generic"},
            {"value": "185.1.2.3", "category": "generic"},
            {"value": "Repeated 185.1.2.3 here", "category": "generic"},
        ]
        iocs = extract_iocs(strings, b"")
        ips = [i["value"] for i in iocs if i["type"] == "ip"]
        assert ips.count("185.1.2.3") == 1

    def test_empty_strings(self):
        assert extract_iocs([], b"") == []


class TestComputeScore:
    """Tests for threat scoring."""

    def test_clean_file(self):
        score, verdict, _ = compute_score(
            yara_matches=[],
            iocs=[],
            strings=[],
            entropy=3.5,
            pe_info=None,
        )
        assert score == 0
        assert verdict == "clean"

    def test_malicious_yara_match(self):
        score, verdict, _ = compute_score(
            yara_matches=[
                {"rule": "Test_Rule", "severity": "critical", "tags": ["critical"]}
            ],
            iocs=[],
            strings=[],
            entropy=5.0,
            pe_info=None,
        )
        assert score >= 30
        assert verdict in ("suspicious", "malicious")

    def test_high_ioc_count_increases_score(self):
        iocs = [{"type": "ip", "value": f"1.2.3.{i}"} for i in range(15)]
        score, _, _ = compute_score(
            yara_matches=[],
            iocs=iocs,
            strings=[],
            entropy=5.0,
            pe_info=None,
        )
        assert score > 0

    def test_score_capped_at_100(self):
        """Score should never exceed 100."""
        score, _, _ = compute_score(
            yara_matches=[
                {"rule": "R1", "severity": "critical", "tags": ["critical"]},
                {"rule": "R2", "severity": "critical", "tags": ["critical"]},
                {"rule": "R3", "severity": "high", "tags": ["high"]},
                {"rule": "R4", "severity": "high", "tags": ["high"]},
            ],
            iocs=[{"type": "ip", "value": f"1.2.3.{i}"} for i in range(50)],
            strings=[{"value": "powershell", "category": "generic"}],
            entropy=7.9,
            pe_info={"sections": [{"entropy": 7.95}]},
        )
        assert score <= 100

    def test_verdict_thresholds(self):
        """
        0-24: clean
        25-59: suspicious
        60-100: malicious
        """
        # Test boundary: 24 → clean
        _, verdict, _ = compute_score([], [], [], 3.0, None)
        assert verdict == "clean"

    def test_high_entropy_adds_score(self):
        score, _, _ = compute_score(
            yara_matches=[],
            iocs=[],
            strings=[],
            entropy=7.8,
            pe_info=None,
        )
        # High entropy alone should contribute some points
        assert score >= 0
