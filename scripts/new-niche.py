#!/usr/bin/env python3
"""All-in-one New Store / Niche launcher for ai-memory-boilerplate + store-crm-boilerplate.

Works for BOTH:
1. Brand-new users (0 setup yet):
   Automatically initializes the unified Obsidian vault (`~/Work/ai-memory`) and installs all 4 skills
   (`ai-memory-kit`, `morocco-cod-marketing`, `crm-catalog`, `product-page-marketing-sections`) via `setup.py`,
   then clones and configures `store-crm-boilerplate`.
2. Existing users adding a 2nd/3rd store (either from this repo or from `<vault>/tools/new-niche.py`):
   Adds the new store to `01 Products/<store>/`, `02 Bases/<store>_Marketing.base`, `02 Bases/Products_Marketing.base`,
   and `PROFILE.md`, clones `store-crm-boilerplate`, creates `~/Pictures/<store>_pics/{staging,uploaded}`,
   writes `~/.config/<store>/catalog-agent.env` (chmod 600), and links `<repo>/AGENTS.md` to the vault.
"""
import argparse
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_STORE_TEMPLATE_URL = "https://github.com/aammo1/store-crm-boilerplate.git"

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
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", raw.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"Invalid store/niche slug: {raw!r}")
    return slug


def default_memory_dir() -> Path:
    script_parent = Path(__file__).resolve().parent
    # If running from inside <vault>/tools/new-niche.py, default to <vault>
    if script_parent.name == "tools" and (script_parent.parent / "PROFILE.md").is_file():
        return script_parent.parent
    return Path.home() / "Work/ai-memory"


def build_store_base(store: str) -> str:
    lines = [
        "filters:",
        "  and:",
        f'    - file.inFolder("01 Products/{store}")',
        "    - 'file.ext == \"md\"'",
        "formulas:",
        "  Product_image: image(cover)",
        "properties:",
        "  formula.Product_image:",
        "    displayName: Product image",
        "views:",
        "  - type: notion-table",
        f"    name: {store} Products",
        "    order:",
    ]
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


def build_tree_lines(items: list[tuple[str, str]]) -> str:
    lines = []
    for idx, (name, comment) in enumerate(items):
        branch = "└──" if idx == len(items) - 1 else "├──"
        pad = " " * max(1, 32 - len(name))
        lines.append(f"{branch} {name}{pad}<- {comment}")
    return "\n".join(lines)


def store_column_values(
    store: str,
    memory_dir: Path,
    repo_dir: Path,
    pics_dir: Path,
    catalog_env_path: Path,
    live_url: str,
) -> dict[str, str]:
    return {
        "**Store Code Repository**": f"`{repo_dir}`",
        "**Marketing Plans (`01 Products`)**": f"`01 Products/{store}/<product>.md`",
        "**Store Base Table (`02 Bases`)**": f"`02 Bases/{store}_Marketing.base`",
        "**Master Base Table (`02 Bases`)**": "`02 Bases/Products_Marketing.base`",
        "**Marketing Template (`00 Templates`)**": "`00 Templates/Product Template.md`",
        "**Product Cover Images (`03 Assets`)**": "`03 Assets/Product images/`",
        "**Product Pictures Folder**": f"`{pics_dir}` (`staging/` & `uploaded/`)",
        "**Hero `01` Reference Image**": f"`{memory_dir}/03 Assets/Reference Heroes/{store}_hero_01.png`",
        "**Hero `01` Live Style URL**": f"`{live_url}`",
        "**Catalog API Env**": f"`{catalog_env_path}`",
        "**Kie.ai Image Generator**": f"`{memory_dir}/tools/kie_generate.py` (env: `~/.config/kie/kie.env`)",
    }


def upsert_profile_store_column(
    profile_path: Path,
    store: str,
    memory_dir: Path,
    repo_dir: Path,
    pics_dir: Path,
    catalog_env_path: Path,
    live_url: str,
) -> None:
    if not profile_path.is_file():
        return
    text = profile_path.read_text(encoding="utf-8")
    col_vals = store_column_values(store, memory_dir, repo_dir, pics_dir, catalog_env_path, live_url)
    col_header = f"`{store}`"

    lines = text.splitlines()
    header_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("| Resource |")), None)
    if header_idx is None:
        return

    header_cells = [c.strip() for c in lines[header_idx].strip().strip("|").split("|")]
    if col_header in header_cells:
        col_index = header_cells.index(col_header)
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("| **"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                row_key = cells[0]
                if row_key in col_vals and col_index < len(cells):
                    cells[col_index] = col_vals[row_key]
                    new_lines.append("| " + " | ".join(cells) + " |")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        updated = "\n".join(new_lines) + "\n"
    else:
        new_lines = []
        for line in lines:
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

    profile_path.write_text(updated, encoding="utf-8")


def clone_store_boilerplate(template_src: str, repo_dir: Path) -> None:
    if repo_dir.exists() and any(repo_dir.iterdir()):
        print(f"SKIP CLONE (already exists): {repo_dir}")
        return
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    src_path = Path(template_src).expanduser()
    if src_path.is_dir():
        print(f"Copying local store-crm-boilerplate from {src_path} -> {repo_dir} ...")
        shutil.copytree(
            src_path,
            repo_dir,
            ignore=shutil.ignore_patterns(".git", "node_modules", ".next", "data", ".env.local", ".env.production.example"),
            dirs_exist_ok=True,
        )
    else:
        print(f"Cloning {template_src} -> {repo_dir} ...")
        subprocess.run(["git", "clone", "--depth", "1", template_src, str(repo_dir)], check=True)
        git_dir = repo_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

    subprocess.run(["git", "init", str(repo_dir)], check=False, stdout=subprocess.DEVNULL)
    print(f"CREATED STORE REPO: {repo_dir}")


def extract_or_create_catalog_env(repo_dir: Path) -> tuple[str, str]:
    """Read CATALOG_AGENT_KEY and CRM_PUBLIC_URL from .env.local / .env / .env.production.example, or generate defaults."""
    key = ""
    url = ""
    for env_name in [".env.local", ".env", ".env.production.example"]:
        env_file = repo_dir / env_name
        if env_file.is_file():
            file_key = ""
            file_url = ""
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if stripped.startswith("CATALOG_AGENT_KEY="):
                    val = stripped.split("=", 1)[1].strip().strip("\"'")
                    if len(val) >= 32:
                        file_key = val
                elif stripped.startswith("CRM_PUBLIC_URL="):
                    val = stripped.split("=", 1)[1].strip().strip("\"'")
                    if val:
                        file_url = val
            if file_key and not key:
                key = file_key
            if file_url and not url:
                url = file_url
            if key and url:
                break
    if not url:
        url = "http://localhost:3000"
    if not key:
        key = secrets.token_hex(32)
        env_local = repo_dir / ".env.local"
        existing = env_local.read_text(encoding="utf-8") if env_local.is_file() else ""
        if "CATALOG_AGENT_KEY=" not in existing:
            with env_local.open("a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(f"CATALOG_AGENT_KEY={key}\n")
    return url, key


def write_catalog_env_file(catalog_env_path: Path, url: str, key: str) -> None:
    catalog_env_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(catalog_env_path.parent, 0o700)
    content = f"CRM_CATALOG_URL={url}\nCRM_CATALOG_KEY={key}\n"
    catalog_env_path.write_text(content, encoding="utf-8")
    os.chmod(catalog_env_path, 0o600)
    print(f"CONFIGURED:    {catalog_env_path} (chmod 600)")


def connect_repo_agents_md(repo_dir: Path, memory_dir: Path) -> None:
    agents_file = repo_dir / "AGENTS.md"
    marker = "## External Memory & Workflow"
    block = (
        f"## External Memory & Workflow\n"
        f"Shared cross-session memory & marketing vault lives in {memory_dir}:\n"
        f"- System Map & Preferences: {memory_dir}/PROFILE.md\n"
        f"- Open Tasks & Log: {memory_dir}/TODO.md\n"
        f"- 10-Step Product Launch SOP: {memory_dir}/LAUNCH-PIPELINE.md\n\n"
    )
    if agents_file.is_file():
        existing = agents_file.read_text(encoding="utf-8")
        if marker in existing:
            return
        agents_file.write_text(block + existing, encoding="utf-8")
    else:
        agents_file.write_text(block, encoding="utf-8")
    print(f"LINKED VAULT:  {agents_file} -> {memory_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-command launcher for a new store/niche (initializes vault & skills if needed + clones store-crm-boilerplate + links everything)."
    )
    parser.add_argument("--store", required=True, help="Store/niche slug (e.g. glow-skin)")
    parser.add_argument("--name", default="Operator", help="Your name for PROFILE.md if initializing the vault for the first time")
    parser.add_argument("--memory-dir", default=str(default_memory_dir()), help="Unified vault path (default: ~/Work/ai-memory)")
    parser.add_argument("--projects-dir", default=str(Path.home() / "Projects"), help="Parent folder for store code repos (default: ~/Projects)")
    parser.add_argument("--repo-dir", help="Explicit target path for the store repo (defaults to <projects-dir>/<store>)")
    parser.add_argument("--pictures-dir", default=str(Path.home() / "Pictures"), help="Parent folder for product pictures (default: ~/Pictures)")
    parser.add_argument("--config-dir", default=str(Path.home() / ".config"), help="Base config directory for secrets (default: ~/.config)")
    parser.add_argument("--skills-dir", default=str(Path.home() / ".agents/skills"), help="Skills directory (default: ~/.agents/skills)")
    parser.add_argument("--store-template", default=DEFAULT_STORE_TEMPLATE_URL, help="Git URL or local path of store-crm-boilerplate")
    parser.add_argument("--answers", help="Optional JSON answers file for non-interactive `npm run new-store -- --answers <file>`")
    parser.add_argument("--skip-npm", action="store_true", help="Clone and wire paths/keys without running npm install or npm run new-store")
    parser.add_argument("--no-store-repo", action="store_true", help="Only register the store in the vault and create pictures folders without cloning store-crm-boilerplate")
    args = parser.parse_args()

    store = sanitize_slug(args.store)
    memory_dir = Path(args.memory_dir).expanduser().resolve()
    projects_dir = Path(args.projects_dir).expanduser().resolve()
    repo_dir = Path(args.repo_dir).expanduser().resolve() if args.repo_dir else (projects_dir / store)
    pics_dir = Path(args.pictures_dir).expanduser().resolve() / f"{store}_pics"
    config_dir = Path(args.config_dir).expanduser().resolve()
    skills_dir = Path(args.skills_dir).expanduser().resolve()
    catalog_env_path = config_dir / store / "catalog-agent.env"

    # Step 1: Ensure Unified Vault & 4 Skills exist (Brand-new user vs. Existing user)
    setup_script = Path(__file__).resolve().parent / "setup.py"
    if not (memory_dir / "PROFILE.md").is_file():
        if not setup_script.is_file():
            sys.exit(f"ERROR: Vault at {memory_dir} is not initialized and setup.py was not found alongside this script.")
        print(f"=== Step 1: First-time setup — Initializing Unified Vault & 4 Skills at {memory_dir} ===")
        subprocess.run(
            [
                sys.executable,
                str(setup_script),
                "--memory-dir",
                str(memory_dir),
                "--name",
                args.name,
                "--stores",
                store,
                "--skills-dir",
                str(skills_dir),
                "--install-skill",
            ],
            check=True,
        )
    else:
        print(f"=== Step 1: Adding store '{store}' to existing Unified Vault at {memory_dir} ===")
        keep_file = memory_dir / "01 Products" / store / ".gitkeep"
        keep_file.parent.mkdir(parents=True, exist_ok=True)
        if not keep_file.exists():
            keep_file.write_text("", encoding="utf-8")
        store_base_path = memory_dir / "02 Bases" / f"{store}_Marketing.base"
        if not store_base_path.exists():
            store_base_path.parent.mkdir(parents=True, exist_ok=True)
            store_base_path.write_text(build_store_base(store), encoding="utf-8")
            print(f"CREATED:       {store_base_path}")
        all_stores = sorted(set(discover_existing_stores(memory_dir) + [store]))
        master_base_path = memory_dir / "02 Bases/Products_Marketing.base"
        master_base_path.write_text(build_master_base(all_stores), encoding="utf-8")
        print(f"UPDATED:       {master_base_path}")

    # Step 2: Create Product Pictures staging/ and uploaded/ folders
    print(f"\n=== Step 2: Creating Product Pictures folders at {pics_dir} ===")
    for sub in ["staging", "uploaded"]:
        sub_dir = pics_dir / sub
        sub_dir.mkdir(parents=True, exist_ok=True)
        print(f"READY:         {sub_dir}")

    # Step 3: Clone & initialize store-crm-boilerplate
    live_url = f"https://{store}.example.com"
    if not args.no_store_repo:
        print(f"\n=== Step 3: Setting up store-crm-boilerplate at {repo_dir} ===")
        clone_store_boilerplate(args.store_template, repo_dir)
        if not args.skip_npm:
            print(f"Running `npm install` in {repo_dir} ...")
            subprocess.run(["npm", "install"], cwd=str(repo_dir), check=True)
            new_store_cmd = ["npm", "run", "new-store"]
            if args.answers:
                answers_path = str(Path(args.answers).expanduser().resolve())
                new_store_cmd.extend(["--", "--answers", answers_path])
            print(f"Running `{' '.join(new_store_cmd)}` in {repo_dir} ...")
            subprocess.run(new_store_cmd, cwd=str(repo_dir), check=True)

        url, key = extract_or_create_catalog_env(repo_dir)
        live_url = url
        write_catalog_env_file(catalog_env_path, url, key)
        connect_repo_agents_md(repo_dir, memory_dir)

    # Step 4: Update PROFILE.md with exact real paths
    print(f"\n=== Step 4: Updating {memory_dir / 'PROFILE.md'} with real paths ===")
    upsert_profile_store_column(
        memory_dir / "PROFILE.md",
        store,
        memory_dir,
        repo_dir,
        pics_dir,
        catalog_env_path,
        live_url,
    )
    print(f"UPDATED:       {memory_dir / 'PROFILE.md'}")

    print(f"\nDone! Store '{store}' is 100% wired:")
    print(f"  - Obsidian Marketing Notes: {memory_dir}/01 Products/{store}/")
    print(f"  - Obsidian Base Table:      {memory_dir}/02 Bases/{store}_Marketing.base")
    print(f"  - Product Pictures Folder:  {pics_dir}/ (staging/ & uploaded/)")
    if not args.no_store_repo:
        print(f"  - Store + CRM Code Repo:    {repo_dir}")
        print(f"  - Catalog API Secret Env:   {catalog_env_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
