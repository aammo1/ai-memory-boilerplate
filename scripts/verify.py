#!/usr/bin/env python3
"""Read-only health and secret-leak checker for a 3-file AI memory directory."""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = ["AGENTS.md", "PROFILE.md", "TODO.md", "PIPELINE.md"]
SECRET_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9_-]{20,}|(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|CATALOG_KEY)\s*=\s*[\"']?[A-Za-z0-9_-]{16,})"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a 3-file AI memory folder.")
    parser.add_argument("--memory-dir", required=True, help="Path to the memory directory")
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    if not memory_dir.is_dir():
        print(f"FAIL: Directory does not exist: {memory_dir}")
        return 2

    failures = []
    for req in REQUIRED_FILES:
        if not (memory_dir / req).is_file():
            failures.append(f"Missing required file: {req}")

    md_files = list(memory_dir.rglob("*.md"))
    for path in md_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SECRET_PATTERN.search(text):
            failures.append(f"Possible secret value detected in {path.name}; store secrets in .env files only")

    for fail in failures:
        print(f"FAIL: {fail}")

    status = "FAIL" if failures else "PASS"
    print(f"{status} memory health check ({len(md_files)} markdown files checked in {memory_dir})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
