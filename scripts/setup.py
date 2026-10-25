#!/usr/bin/env python3
"""Setup script for ai-memory-boilerplate.

Initializes an all-in-one AI Memory + Obsidian Marketing Vault containing:
- Root memory files: AGENTS.md, PROFILE.md, TODO.md, LAUNCH-PIPELINE.md
- Marketing folders:
  - 00 Templates/Product Template.md
  - 01 Products/<store>/
  - 02 Bases/Products_Marketing.base (with All Products + per-store view tabs) + 02 Bases/<store>_Marketing.base
  - 03 Assets/Product images/ + 03 Assets/Reference Heroes/
- Obsidian config (.obsidian/) with Bases, GoodBases (notion-table), Templates, and locked property types (types.json)
- Crash-safe Kie.ai batch generator (tools/kie_generate.py + tools/test_kie_generate.py)
- Git repository initialization + optional `ai-memory-kit` skill installation
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
TOOLS_DIR = REPO_ROOT / "tools"
SKILLS_SRC_DIR = REPO_ROOT / "skill"
SKILL_TEMPLATE = SKILLS_SRC_DIR / "ai-memory-kit/SKILL.md.template"
BUNDLED_STATIC_SKILLS = [
    "morocco-cod-marketing",
    "crm-catalog",
    "product-page-marketing-sections",
]

OBSIDIAN_CORE_PLUGINS = {
    "file-explorer": True,
    "global-search": True,
    "switcher": True,
    "graph": True,
    "backlink": True,
    "canvas": True,
    "outgoing-link": True,
    "tag-pane": True,
    "footnotes": False,
    "properties": True,
    "page-preview": True,
    "daily-notes": True,
    "templates": True,
    "note-composer": True,
    "command-palette": True,
    "slash-command": False,
    "editor-status": True,
    "bookmarks": True,
    "markdown-importer": False,
    "zk-prefixer": False,
    "random-note": False,
    "outline": True,
    "word-count": True,
    "slides": False,
    "audio-recorder": False,
    "workspaces": False,
    "file-recovery": True,
    "publish": False,
    "sync": True,
    "bases": True,
    "webviewer": False,
}

OBSIDIAN_PROPERTY_TYPES = {
    "types": {
        "cover": "text",
        "🛫 find_product_methods": "multitext",
        "🛫 categories": "multitext",
        "🛫 assets": "multitext",
        "✈️Product_Potentials": "multitext",
        "✈️Reputation_Reviews_Mining": "text",
        "✈️Concurrences_Analyses": "text",
        "🎡Problems_defaut_pain_point": "text",
        "🎡solution_feature_benifits_special_Competitive_advantage": "text",
        "🎡targeted_audiance_pain_point_benifits": "text",
        "🚂human_desir_Angle_marketing": "multitext",
        "🚂emotion_angle": "multitext",
        "🚂Copy_Techniques": "multitext",
        "🌟Hook_Type": "multitext",
        "🌟Creative_Typee_Techniques": "multitext",
        "🌟Action_plan": "text",
        "📝NOTES": "text",
    }
}

BASE_COLUMNS = [
    "formula.Product_image",
    "🛫 find_product_methods",
    "🛫 assets",
    "🛫 categories",
    "✈️Product_Potentials",
    "✈️Reputation_Reviews_Mining",
    "✈️Concurrences_Analyses",
    "🎡Problems_defaut_pain_point",
    "🎡solution_feature_benifits_special_Competitive_advantage",
    "🎡targeted_audiance_pain_point_benifits",
    "🚂human_desir_Angle_marketing",
    "🚂emotion_angle",
    "🚂Copy_Techniques",
    "🌟Creative_Typee_Techniques",
    "🌟Hook_Type",
    "🌟Action_plan",
    "📝NOTES",
    "cover",
]


def sanitize_slug(raw: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", raw.strip()).strip("-")
    if not slug:
        raise ValueError(f"Invalid store/niche slug: {raw!r}")
    return slug


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


def store_column_values(store: str, memory_dir: Path) -> dict[str, str]:
    return {
        "**Store Code Repository**": f"`/path/to/{store}-repo`",
        "**Marketing Plans (`01 Products`)**": f"`01 Products/{store}/<product>.md`",
        "**Store Base Table (`02 Bases`)**": f"`02 Bases/{store}_Marketing.base`",
        "**Master Base Table (`02 Bases`)**": "`02 Bases/Products_Marketing.base`",
        "**Marketing Template (`00 Templates`)**": "`00 Templates/Product Template.md`",
        "**Product Cover Images (`03 Assets`)**": "`03 Assets/Product images/`",
        "**Product Pictures Folder**": f"`/path/to/{store}_pics` (`staging/` & `uploaded/`)",
        "**Hero `01` Reference Image**": f"`{memory_dir}/03 Assets/Reference Heroes/{store}_hero_01.png`",
        "**Hero `01` Live Style URL**": f"`https://{store}.example.com`",
        "**Catalog API Env**": f"`~/.config/{store}/catalog-agent.env`",
        "**Kie.ai Image Generator**": f"`{memory_dir}/tools/kie_generate.py` (env: `~/.config/kie/kie.env`)",
    }


def build_store_table(stores: list[str], memory_dir: Path) -> str:
    headers = ["Resource"] + [f"`{s}`" for s in stores]
    sep = ["---"] * len(headers)
    per_store = [store_column_values(s, memory_dir) for s in stores]
    row_keys = list(per_store[0].keys())

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for key in row_keys:
        row = [key] + [col[key] for col in per_store]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_tree_lines(items: list[tuple[str, str]]) -> str:
    lines = []
    for idx, (name, comment) in enumerate(items):
        branch = "└──" if idx == len(items) - 1 else "├──"
        pad = " " * max(1, 32 - len(name))
        lines.append(f"{branch} {name}{pad}<- {comment}")
    return "\n".join(lines)


def build_master_base(stores: list[str]) -> str:
    all_order = ["formula.Product_image", "file.folder"] + BASE_COLUMNS[1:]
    lines = [
        "filters:",
        "  and:",
        '    - file.inFolder("01 Products")',
        "    - 'file.ext == \"md\"'",
        "formulas:",
        "  Product_image: image(cover)",
        "properties:",
        "  formula.Product_image:",
        "    displayName: Product image",
        "  file.folder:",
        "    displayName: Store folder",
        "views:",
        "  - type: notion-table",
        "    name: All Products Table",
        "    order:",
    ]
    for col in all_order:
        lines.append(f"      - {col}")
    lines.extend([
        "    openMode: panel",
        "    wrapCells: true",
        "    verticalLines: true",
        "    image: formula.Product_image",
        "    imageFit: contain",
    ])

    for store in stores:
        lines.extend([
            "  - type: notion-table",
            f"    name: {store} Products",
            "    filters:",
            "      and:",
            f'        - file.inFolder("01 Products/{store}")',
            "    order:",
        ])
        for col in BASE_COLUMNS:
            lines.append(f"      - {col}")
        lines.extend([
            "    openMode: panel",
            "    wrapCells: true",
            "    verticalLines: true",
            "    image: formula.Product_image",
            "    imageFit: contain",
        ])
    return "\n".join(lines) + "\n"


def discover_existing_stores(memory_dir: Path) -> list[str]:
    products_dir = memory_dir / "01 Products"
    if not products_dir.is_dir():
        return []
    return sorted(
        d.name for d in products_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )


def update_profile_with_store(profile_path: Path, store: str, memory_dir: Path, dry_run: bool) -> str:
    if not profile_path.is_file():
        return f"SKIP (missing): {profile_path}"
    text = profile_path.read_text(encoding="utf-8")
    col_header = f"`{store}`"
    if f"| {col_header} |" in text:
        return f"SKIP (already in PROFILE.md): {store}"

    col_vals = store_column_values(store, memory_dir)
    new_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Resource |"):
            new_lines.append(f"{stripped} {col_header} |")
        elif re.match(r"^\|\s*---", stripped):
            new_lines.append(f"{stripped} --- |")
        elif stripped.startswith("| **"):
            matched_val = None
            for key, val in col_vals.items():
                if stripped.startswith(f"| {key} |"):
                    matched_val = val
                    break
            if matched_val is not None:
                new_lines.append(f"{stripped} {matched_val} |")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    updated = "\n".join(new_lines) + "\n"

    # Also refresh the 01 Products/ and 02 Bases/ tree blocks if present
    all_stores = sorted(set(discover_existing_stores(memory_dir) + [store]))
    if all_stores:
        products_tree = build_tree_lines([(f"{s}/", f"Marketing plan notes for {s}") for s in all_stores])
        bases_tree = build_tree_lines([(f"{s}_Marketing.base", f"Filtered Obsidian Base table for {s}") for s in all_stores])
        updated = re.sub(
            r"(01 Products/\n)(?:[├└]── .*\n)+",
            f"\\g<1>{products_tree}\n",
            updated,
        )
        updated = re.sub(
            r"(├── Products_Marketing\.base\s+<- Master Obsidian Base table across all stores/niches\n)(?:[├└]── .*\n)+",
            f"\\g<1>{bases_tree}\n",
            updated,
        )

    if dry_run:
        return f"WOULD UPDATE:  {profile_path} (added column `{store}`)"
    profile_path.write_text(updated, encoding="utf-8")
    return f"UPDATED:       {profile_path} (added column `{store}`)"


def scaffold_store(memory_dir: Path, store: str, base_tpl: Path, force: bool, dry_run: bool) -> list[str]:
    results = []
    keep_file = memory_dir / "01 Products" / store / ".gitkeep"
    results.append(write_safe(keep_file, "", force, dry_run))

    store_base = memory_dir / "02 Bases" / f"{store}_Marketing.base"
    base_content = render(
        base_tpl,
        {
            "PRODUCTS_FOLDER": f"01 Products/{store}",
            "VIEW_NAME": f"{store} Products",
        },
    )
    results.append(write_safe(store_base, base_content, force, dry_run))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Initialize or extend your unified AI Memory + Obsidian Marketing Vault."
    )
    parser.add_argument("--memory-dir", required=True, help="Target directory for your unified vault (e.g. ~/Work/ai-memory)")
    parser.add_argument("--name", default="Operator", help="Your name or handle for PROFILE.md and AGENTS.md")
    parser.add_argument(
        "--stores",
        default="store-a,store-b",
        help="Comma-separated store/niche slugs to scaffold (default: store-a,store-b; e.g. zehri,hellobaby)",
    )
    parser.add_argument(
        "--add-store",
        help="Add a single new store/niche subfolder, Obsidian Base table, and PROFILE.md column to an existing vault",
    )
    parser.add_argument(
        "--install-skill",
        "--install-skills",
        dest="install_skill",
        action="store_true",
        help="Install all 4 bundled skills (ai-memory-kit, morocco-cod-marketing, crm-catalog, product-page-marketing-sections) to ~/.agents/skills/",
    )
    parser.add_argument("--skills-dir", default=str(Path.home() / ".agents/skills"), help="Base skills directory (default: ~/.agents/skills)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing to disk")
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir).expanduser().resolve()
    base_tpl = TEMPLATES_DIR / "Products_Marketing.base.template"

    if args.add_store:
        store_slug = sanitize_slug(args.add_store)
        print(f"=== Adding store/niche '{store_slug}' to: {memory_dir} ===")
        for line in scaffold_store(memory_dir, store_slug, base_tpl, args.force, args.dry_run):
            print(line)
        print(update_profile_with_store(memory_dir / "PROFILE.md", store_slug, memory_dir, args.dry_run))
        all_stores = sorted(set(discover_existing_stores(memory_dir) + [store_slug]))
        master_base_path = memory_dir / "02 Bases/Products_Marketing.base"
        print(write_safe(master_base_path, build_master_base(all_stores), True, args.dry_run))
        print(f"\nDone! Store `{store_slug}` is ready in 01 Products/{store_slug}/, 02 Bases/, and PROFILE.md.")
        return 0

    stores = [sanitize_slug(s) for s in args.stores.split(",") if s.strip()]
    if not stores:
        stores = ["store-a"]

    today = datetime.date.today().isoformat()
    products_tree = build_tree_lines([(f"{s}/", f"Marketing plan notes for {s}") for s in stores])
    bases_tree = build_tree_lines([(f"{s}_Marketing.base", f"Filtered Obsidian Base table for {s}") for s in stores])

    replacements = {
        "USER_NAME": args.name,
        "MEMORY_DIR": str(memory_dir),
        "DATE": today,
        "FIRST_STORE": stores[0],
        "STORE_PATHS_TABLE": build_store_table(stores, memory_dir),
        "PRODUCTS_TREE_LINES": products_tree,
        "BASES_TREE_LINES": bases_tree,
    }

    print(f"=== Setting up Unified AI Memory & Marketing Vault at: {memory_dir} ===")
    for name in ["AGENTS.md", "PROFILE.md", "TODO.md", "LAUNCH-PIPELINE.md"]:
        tpl = TEMPLATES_DIR / f"{name}.template"
        out = memory_dir / name
        print(write_safe(out, render(tpl, replacements), args.force, args.dry_run))

    # 00 Templates/Product Template.md
    product_tpl = TEMPLATES_DIR / "Product Template.md.template"
    print(copy_safe(product_tpl, memory_dir / "00 Templates/Product Template.md", args.force, args.dry_run))

    # 02 Bases/Products_Marketing.base (Master table + per-store view tabs)
    print(write_safe(memory_dir / "02 Bases/Products_Marketing.base", build_master_base(stores), args.force, args.dry_run))

    # Per-store 01 Products/<store>/ and 02 Bases/<store>_Marketing.base
    for store in stores:
        for line in scaffold_store(memory_dir, store, base_tpl, args.force, args.dry_run):
            print(line)

    # 03 Assets/Product images/ and 03 Assets/Reference Heroes/
    print(write_safe(memory_dir / "03 Assets/Product images/.gitkeep", "", args.force, args.dry_run))
    heroes_readme = memory_dir / "03 Assets/Reference Heroes/README.md"
    heroes_examples = ", ".join(f"`{s}_hero_01.png`" for s in stores)
    heroes_text = (
        "# 03 Assets / Reference Heroes\n\n"
        f"Place each store's Hero `01` style reference image here (e.g. {heroes_examples}).\n"
        "Pipeline Steps 4 & 5 pass this reference image to `kie_generate.py` so every product's main hero photo matches the store look.\n"
    )
    print(write_safe(heroes_readme, heroes_text, args.force, args.dry_run))

    # Copy tools/kie_generate.py and tools/test_kie_generate.py
    for tool_name in ["kie_generate.py", "test_kie_generate.py"]:
        print(copy_safe(TOOLS_DIR / tool_name, memory_dir / "tools" / tool_name, args.force, args.dry_run))

    # Configure .obsidian/ for out-of-the-box Bases + GoodBases (notion-table) + Templates + Property Types
    print(
        write_safe(
            memory_dir / ".obsidian/templates.json",
            json.dumps({"folder": "00 Templates"}, indent=2) + "\n",
            args.force,
            args.dry_run,
        )
    )
    print(
        write_safe(
            memory_dir / ".obsidian/core-plugins.json",
            json.dumps(OBSIDIAN_CORE_PLUGINS, indent=2) + "\n",
            args.force,
            args.dry_run,
        )
    )
    print(
        write_safe(
            memory_dir / ".obsidian/community-plugins.json",
            json.dumps(["good-bases"], indent=2) + "\n",
            args.force,
            args.dry_run,
        )
    )
    print(
        write_safe(
            memory_dir / ".obsidian/types.json",
            json.dumps(OBSIDIAN_PROPERTY_TYPES, indent=2, ensure_ascii=False) + "\n",
            args.force,
            args.dry_run,
        )
    )
    print(
        write_safe(
            memory_dir / ".obsidian/app.json",
            json.dumps({"promptDelete": False}, indent=2) + "\n",
            args.force,
            args.dry_run,
        )
    )
    good_bases_src = TEMPLATES_DIR / "obsidian/plugins/good-bases"
    for plugin_file in ["manifest.json", "main.js", "styles.css"]:
        print(
            copy_safe(
                good_bases_src / plugin_file,
                memory_dir / ".obsidian/plugins/good-bases" / plugin_file,
                args.force,
                args.dry_run,
            )
        )

    # Vault .gitignore so Obsidian workspace state and caches don't pollute git
    vault_gitignore = (
        ".obsidian/workspace.json\n"
        ".obsidian/workspace-mobile.json\n"
        "__pycache__/\n"
        "*.pyc\n"
        ".DS_Store\n"
        ".env\n"
        ".env.*\n"
    )
    print(write_safe(memory_dir / ".gitignore", vault_gitignore, args.force, args.dry_run))

    if not args.dry_run and not (memory_dir / ".git").exists():
        subprocess.run(["git", "init", str(memory_dir)], check=False, stdout=subprocess.DEVNULL)
        print(f"GIT INIT:      {memory_dir}/.git")

    if args.install_skill:
        skills_root = Path(args.skills_dir).expanduser().resolve()
        skill_dest = skills_root / "ai-memory-kit/SKILL.md"
        print(write_safe(skill_dest, render(SKILL_TEMPLATE, replacements), args.force, args.dry_run))
        for static_skill in BUNDLED_STATIC_SKILLS:
            src_dir = SKILLS_SRC_DIR / static_skill
            if src_dir.is_dir():
                for src_file in sorted(src_dir.rglob("*")):
                    if src_file.is_file():
                        rel_path = src_file.relative_to(src_dir)
                        dest_file = skills_root / static_skill / rel_path
                        print(copy_safe(src_file, dest_file, args.force, args.dry_run))

    print("\nDone! Next steps:")
    print(f"  1. Open '{memory_dir}' directly in Obsidian (Bases, GoodBases & Templates are pre-configured).")
    print(f"  2. Edit {memory_dir}/PROFILE.md with your real store/project paths.")
    print(f"  3. Drop your store hero reference images into '{memory_dir}/03 Assets/Reference Heroes/'.")
    print(f"  4. Verify vault health: python3 scripts/verify.py --memory-dir \"{memory_dir}\"")
    if args.install_skill:
        print("  5. In any folder on your machine, tell your AI: 'use ai-memory-kit'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
