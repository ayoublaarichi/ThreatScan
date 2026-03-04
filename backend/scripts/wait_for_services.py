#!/usr/bin/env python3
"""
Wait for dependent services (PostgreSQL, Redis, MinIO) to become available.

Usage:
    python scripts/wait_for_services.py [--timeout 30]
"""

import socket
import sys
import time
import argparse
import os


SERVICES = [
    ("PostgreSQL", os.getenv("POSTGRES_HOST", "localhost"), int(os.getenv("POSTGRES_PORT", "5432"))),
    ("Redis", "localhost", 6379),
    ("MinIO", "localhost", 9000),
]


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is accepting connections."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def wait_for_services(timeout: int = 60):
    """Wait until all services are reachable."""
    start = time.time()
    pending = list(SERVICES)

    while pending and (time.time() - start) < timeout:
        still_pending = []
        for name, host, port in pending:
            if check_port(host, port):
                elapsed = time.time() - start
                print(f"  ✓ {name} ({host}:{port}) ready [{elapsed:.1f}s]")
            else:
                still_pending.append((name, host, port))

        pending = still_pending
        if pending:
            time.sleep(1)

    if pending:
        for name, host, port in pending:
            print(f"  ✗ {name} ({host}:{port}) NOT ready after {timeout}s")
        sys.exit(1)
    else:
        print(f"\nAll services ready in {time.time() - start:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Wait for dependent services")
    parser.add_argument("--timeout", type=int, default=60, help="Max wait time in seconds")
    args = parser.parse_args()

    print("Waiting for services…")
    wait_for_services(args.timeout)


if __name__ == "__main__":
    main()
