#!/usr/bin/env python3
"""Setup script for ai-memory-boilerplate.

Creates a clean 3-file external memory folder (PROFILE.md, TODO.md, PIPELINE.md + AGENTS.md),
initializes Git inside it, and optionally installs the `ai-memory-kit` skill into ~/.agents/skills/.
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
SKILL_TEMPLATE = REPO_ROOT / "skill/ai-memory-kit/SKILL.md.template"


def render(template_path: Path, replacements: dict[str, str]) -> str:
    content = template_path.read_text(encoding="utf-8")
    for key, val in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", val)
    return content


def write_safe(dest: Path, content: str, force: bool, dry_run: bool) -> str:
    if dest.exists() and not force:
        return f"SKIP (exists): {dest}"
    if dry_run:
        return f"WOULD WRITE:   {dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return f"CREATED:       {dest}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize your 3-file AI Memory folder and optional skill.")
    parser.add_argument("--memory-dir", required=True, help="Target directory for your memory files (e.g. ~/Work/ai-memory)")
    parser.add_argument("--name", default="Developer", help="Your name or handle for PROFILE.md and AGENTS.md")
    parser.add_argument("--install-skill", action="store_true", help="Install the ai-memory-kit skill to ~/.agents/skills/ai-memory-kit/")
    parser.add_argument("--skills-dir", default=str(Path.home() / ".agents/skills"), help="Base skills directory (default: ~/.agents/skills)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing to disk")
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    today = datetime.date.today().isoformat()
    replacements = {
        "USER_NAME": args.name,
        "MEMORY_DIR": str(memory_dir),
        "DATE": today,
    }

    print(f"=== Setting up AI Memory at: {memory_dir} ===")
    for name in ["AGENTS.md", "PROFILE.md", "TODO.md", "PIPELINE.md"]:
        tpl = TEMPLATES_DIR / f"{name}.template"
        out = memory_dir / name
        print(write_safe(out, render(tpl, replacements), args.force, args.dry_run))

    if not args.dry_run and not (memory_dir / ".git").exists():
        subprocess.run(["git", "init", str(memory_dir)], check=False, stdout=subprocess.DEVNULL)
        print(f"GIT INIT:      {memory_dir}/.git")

    if args.install_skill:
        skill_dest = Path(args.skills_dir).expanduser().resolve() / "ai-memory-kit/SKILL.md"
        print(write_safe(skill_dest, render(SKILL_TEMPLATE, replacements), args.force, args.dry_run))

    print("\nDone! Next steps:")
    print(f"  1. Edit {memory_dir}/PROFILE.md with your real project paths.")
    print(f"  2. Run: python3 scripts/verify.py --memory-dir \"{memory_dir}\"")
    if args.install_skill:
        print("  3. In any folder on your machine, tell your AI: 'use ai-memory-kit'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
