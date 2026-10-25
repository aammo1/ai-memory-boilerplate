#!/usr/bin/env python3
"""Setup script for ai-memory-boilerplate.

Creates a clean 3-file external memory folder (PROFILE.md, TODO.md, LAUNCH-PIPELINE.md + AGENTS.md),
copies the crash-safe Kie.ai batch generator (tools/kie_generate.py), creates 03 - Reference Heroes/,
initializes Git inside the memory folder, and optionally installs the `ai-memory-kit` skill.
"""
import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
TOOLS_DIR = REPO_ROOT / "tools"
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


def copy_safe(src: Path, dest: Path, force: bool, dry_run: bool) -> str:
    if dest.exists() and not force:
        return f"SKIP (exists): {dest}"
    if dry_run:
        return f"WOULD COPY:    {dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return f"COPIED:        {dest}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize your 3-file AI Memory folder and optional skill.")
    parser.add_argument("--memory-dir", required=True, help="Target directory for your memory files (e.g. ~/Work/ai-memory)")
    parser.add_argument("--name", default="Operator", help="Your name or handle for PROFILE.md and AGENTS.md")
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
    for name in ["AGENTS.md", "PROFILE.md", "TODO.md", "LAUNCH-PIPELINE.md"]:
        tpl = TEMPLATES_DIR / f"{name}.template"
        out = memory_dir / name
        print(write_safe(out, render(tpl, replacements), args.force, args.dry_run))

    # Create 03 - Reference Heroes folder
    heroes_readme = memory_dir / "03 - Reference Heroes/README.md"
    heroes_text = (
        "# 03 - Reference Heroes\n\n"
        "Place each store's Hero `01` style reference image here (e.g. `store_a_hero_01.png`, `store_b_hero_01.png`).\n"
        "Pipeline Steps 4 & 5 pass this reference image to `kie_generate.py` so every product's main hero photo matches the store look.\n"
    )
    print(write_safe(heroes_readme, heroes_text, args.force, args.dry_run))

    # Copy tools/kie_generate.py and tools/test_kie_generate.py
    for tool_name in ["kie_generate.py", "test_kie_generate.py"]:
        print(copy_safe(TOOLS_DIR / tool_name, memory_dir / "tools" / tool_name, args.force, args.dry_run))

    if not args.dry_run and not (memory_dir / ".git").exists():
        subprocess.run(["git", "init", str(memory_dir)], check=False, stdout=subprocess.DEVNULL)
        print(f"GIT INIT:      {memory_dir}/.git")

    if args.install_skill:
        skill_dest = Path(args.skills_dir).expanduser().resolve() / "ai-memory-kit/SKILL.md"
        print(write_safe(skill_dest, render(SKILL_TEMPLATE, replacements), args.force, args.dry_run))

    print("\nDone! Next steps:")
    print(f"  1. Edit {memory_dir}/PROFILE.md with your real store/project paths.")
    print(f"  2. Drop your store hero reference images into '{memory_dir}/03 - Reference Heroes/'.")
    print(f"  3. Verify setup: python3 scripts/verify.py --memory-dir \"{memory_dir}\"")
    if args.install_skill:
        print("  4. In any folder on your machine, tell your AI: 'use ai-memory-kit'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
