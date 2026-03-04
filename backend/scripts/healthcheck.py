#!/usr/bin/env python3
"""
Health check script for Docker/Kubernetes probes.

Exit code 0 = healthy, 1 = unhealthy.

Usage:
    python scripts/healthcheck.py
"""

import sys
import urllib.request


def main():
    url = "http://localhost:8000/api/v1/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print("OK")
                sys.exit(0)
            else:
                print(f"UNHEALTHY: status {resp.status}")
                sys.exit(1)
    except Exception as e:
        print(f"UNHEALTHY: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
