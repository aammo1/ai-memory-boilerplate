#!/usr/bin/env python3
"""Read-only health, structure, YAML schema, cover-link, and secret-leak checker for a unified AI Memory & Marketing Vault."""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = [
    "AGENTS.md",
    "PROFILE.md",
    "TODO.md",
    "LAUNCH-PIPELINE.md",
    "00 Templates/Product Template.md",
    "02 Bases/Products_Marketing.base",
    ".obsidian/types.json",
    ".obsidian/plugins/good-bases/manifest.json",
    ".obsidian/plugins/good-bases/main.js",
    ".obsidian/plugins/good-bases/styles.css",
    "tools/kie_generate.py",
    "tools/new-niche.py",
]

REQUIRED_DIRS = [
    "00 Templates",
    "01 Products",
    "02 Bases",
    "03 Assets/Product images",
    "03 Assets/Reference Heroes",
]

SECRET_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9_-]{20,}|(?:KIE_API_KEY|DEEPSEEK_API_KEY|API_KEY|SECRET_KEY|ACCESS_TOKEN|CATALOG_KEY)\s*=\s*[\"']?[A-Za-z0-9_-]{16,})"
)

TOP_LEVEL_KEY_PATTERN = re.compile(r"^([^\s:#-][^:]*):")
COVER_LINE_PATTERN = re.compile(r"^cover:\s*(.*?)\s*$", re.MULTILINE)
WIKILINK_INNER_PATTERN = re.compile(r"^\[\[([^\]|]+)(?:\|[^\]]+)?\]\]$")


def extract_frontmatter_keys(frontmatter: str) -> tuple[list[str], list[str]]:
    seen = []
    duplicates = []
    for line in frontmatter.splitlines():
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match:
            key = match.group(1).strip()
            if key in seen and key not in duplicates:
                duplicates.append(key)
            seen.append(key)
    return seen, duplicates


def load_template_keys(template_path: Path) -> list[str]:
    if not template_path.is_file():
        return []
    text = template_path.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---\n"):
        return []
    end_idx = text.find("\n---", 4)
    if end_idx == -1:
        return []
    keys, _ = extract_frontmatter_keys(text[4:end_idx])
    return keys


def validate_product_note(note_path: Path, memory_dir: Path, required_keys: list[str]) -> list[str]:
    issues = []
    text = note_path.read_text(encoding="utf-8", errors="ignore")
    rel = note_path.relative_to(memory_dir)

    if not text.startswith("---\n"):
        issues.append(f"{rel}: Missing opening YAML frontmatter delimiter ('---')")
        return issues

    end_idx = text.find("\n---", 4)
    if end_idx == -1:
        issues.append(f"{rel}: Missing closing YAML frontmatter delimiter ('---')")
        return issues

    frontmatter = text[4:end_idx]
    keys, duplicates = extract_frontmatter_keys(frontmatter)

    for dup in duplicates:
        issues.append(f"{rel}: Duplicate YAML frontmatter key '{dup}'")

    for req_key in required_keys:
        if req_key not in keys:
            issues.append(f"{rel}: Missing required template property '{req_key}'")

    cover_match = COVER_LINE_PATTERN.search(frontmatter)
    if cover_match:
        raw_val = cover_match.group(1).strip()
        if raw_val and raw_val not in {'""', "''", "null", "~"}:
            unquoted = raw_val.strip("\"'").strip()
            wiki_match = WIKILINK_INNER_PATTERN.match(unquoted)
            if not wiki_match:
                issues.append(
                    f"{rel}: Invalid cover format ({raw_val}); must be a vault wikilink like \"[[03 Assets/Product images/file.webp]]\""
                )
            else:
                cover_rel = wiki_match.group(1).strip()
                if not (memory_dir / cover_rel).is_file():
                    issues.append(f"{rel}: Broken cover image wikilink -> '{cover_rel}' does not exist in vault")

    return issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify a unified AI Memory + Obsidian Marketing Vault.")
    parser.add_argument("--memory-dir", required=True, help="Path to the unified vault directory")
    args = parser.parse_args(argv)

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    if not memory_dir.is_dir():
        print(f"FAIL: Directory does not exist: {memory_dir}")
        return 2

    failures = []
    for req in REQUIRED_FILES:
        if not (memory_dir / req).is_file():
            failures.append(f"Missing required file: {req}")

    for req_dir in REQUIRED_DIRS:
        if not (memory_dir / req_dir).is_dir():
            failures.append(f"Missing required directory: {req_dir}/")

    md_files = list(memory_dir.rglob("*.md"))
    for path in md_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SECRET_PATTERN.search(text):
            failures.append(f"Possible secret value detected in {path.relative_to(memory_dir)}; store secrets in .env files only")

    template_keys = load_template_keys(memory_dir / "00 Templates/Product Template.md")
    products_dir = memory_dir / "01 Products"
    product_notes = list(products_dir.rglob("*.md")) if products_dir.is_dir() else []
    for note_path in product_notes:
        failures.extend(validate_product_note(note_path, memory_dir, template_keys))

    base_files = list((memory_dir / "02 Bases").glob("*.base")) if (memory_dir / "02 Bases").is_dir() else []

    for fail in failures:
        print(f"FAIL: {fail}")

    status = "FAIL" if failures else "PASS"
    print(
        f"{status} unified vault health check "
        f"({len(md_files)} markdown files, {len(product_notes)} product notes, {len(base_files)} Obsidian bases verified in {memory_dir})"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
