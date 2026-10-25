# ai-memory-boilerplate

An **all-in-one AI External Memory + Obsidian Marketing Vault boilerplate** with an **on-demand skill (`ai-memory-kit`)** for AI coding agents (**Antigravity, Claude Code, Codex, DSH, OpenCode, Cursor**).

Instead of switching between separate Obsidian vaults for your AI memory and each store/niche (`STORE_A_vault`, `STORE_B_vault`, `AI_MEMORY_vault`), **`ai-memory-boilerplate`** unifies everything into **one structured Obsidian vault**:
- **4 plain Markdown memory files** (`AGENTS.md`, `PROFILE.md`, `TODO.md`, `LAUNCH-PIPELINE.md`) at the root for zero-friction AI context.
- **Built-in multi-store Obsidian Marketing Vault folders** (`00 Templates/`, `01 Products/<store>/`, `02 Bases/`, `03 Assets/`) pre-configured with Obsidian Bases tables and cover images.
- **Crash-safe Kie.ai image generator** (`tools/kie_generate.py`) with `flock` locking and offline tests.
- **4 Bundled Skills (`skill/`)** installed in one command (`--install-skill`):
  - **`ai-memory-kit`** — on-demand vault manager, task tracker, and new-store onboarder from any folder.
  - **`morocco-cod-marketing`** — 3-checkpoint Moroccan COD strategy, 6 static ads, optional video scripts, and 4 gallery prompts saved directly into `01 Products/<store>/`.
  - **`crm-catalog`** — live catalog client (Contract v2) for [`store-crm-boilerplate`](https://github.com/aammo1/store-crm-boilerplate) supporting single-SKU (`standard`) and multi-option products across any niche.
  - **`product-page-marketing-sections`** — mobile-first custom product-page section builder (`src/custom/`) with 26 design recipes.

---

## How It Works (One Unified Vault)

```text
your-memory-vault/
├── .obsidian/                           # Pre-configured for Obsidian Bases + 00 Templates
├── AGENTS.md                            # Boot rules when opening the vault directly
├── PROFILE.md                           # Identity, multi-store/niche paths table, and AI style rules
├── TODO.md                              # Single open task queue + recent completed changelog
├── LAUNCH-PIPELINE.md                   # End-to-end 10-step product launch SOP (Steps 0 to 10)
├── 00 Templates/
│   └── Product Template.md              # Shared YAML schema & choice catalog (angles, emotions, hooks, copy)
├── 01 Products/
│   ├── store-a/                         # Per-store / per-niche product marketing notes
│   └── store-b/
├── 02 Bases/
│   ├── Products_Marketing.base          # Master Obsidian Base table across all stores/niches
│   ├── store-a_Marketing.base           # Filtered Obsidian Base table for store-a
│   └── store-b_Marketing.base           # Filtered Obsidian Base table for store-b
├── 03 Assets/
│   ├── Product images/                  # Product cover images referenced by [[03 Assets/Product images/...]]
│   └── Reference Heroes/                # Store Hero 01 style reference images for Kie.ai
└── tools/
    ├── kie_generate.py                  # Crash-safe, batch-capable Kie.ai image generator (with flock locking)
    └── test_kie_generate.py             # 14 offline regression tests (zero API cost)
```

### Why This Unified Architecture Works Better
1. **One Obsidian Vault for Everything:** Never switch vaults again. Manage all your stores, niches, product marketing plans, visual Obsidian Base tables, and AI task queues in one window.
2. **Multi-Store & Multi-Niche Ready:** Each brand/niche gets its own `01 Products/<store>/` folder and dedicated `02 Bases/<store>_Marketing.base` table while sharing `00 Templates/Product Template.md` and `03 Assets/Product images/`.
3. **Zero Global Pollution:** No global `~/.claude/CLAUDE.md` or `~/.dsh/AGENTS.md` forcing unrelated side-projects to load e-commerce rules. Only projects you choose connect to your vault.
4. **Call From Any Folder (`ai-memory-kit` skill):** Open any folder on your laptop and say *"use `ai-memory-kit`"* to check tasks, create a marketing plan in `01 Products/<store>/`, or onboard a new store/niche.
5. **Resumable Pipelines (`LAUNCH-PIPELINE.md` + `launch-state.json`):** Multi-step product launches track step completion and image slots on disk under an exclusive `flock` lock so interrupted sessions resume without repeating paid API calls.

---

## Quick Start (1 Command — Moroccan COD Operator)

### Scope & Prerequisites
- **Target Market:** Purpose-built for **Moroccan Cash-on-Delivery (COD)** e-commerce (`+212` mobile validation, integer `MAD`, `fr`/`ar` RTL storefront + French CRM back-office, Ozon Express Morocco or `mock` courier via [`store-crm-boilerplate`](https://github.com/aammo1/store-crm-boilerplate)).
- **OS & Runtime:** **Linux, macOS, or Windows WSL2** (`kie_generate.py` uses Unix `fcntl.flock`), **Python 3.11+**, **Astral `uv`** (`curl -LsSf https://astral.sh/uv/install.sh | sh`), **Node.js 22+**, and **Git**.
- **Obsidian (`>= 1.10.2`):** On first vault open, click *Settings → Community plugins → Turn on community plugins* so the pre-bundled **GoodBases** (`notion-table`) plugin renders `02 Bases/*.base`.
- **Optional Paid / External Integrations:**
  - **Steps 4–6 (AI Gallery & Static Ads):** Put `KIE_API_KEY=<your-key>` inside `~/.config/kie/kie.env` (`chmod 600`).
  - **Step 10 (Paused Meta Ads Drafts):** Requires a configured Meta Ads MCP server in your AI client (Steps 0–9 work without it).

If you are a **brand-new user** starting from zero, clone only this repository and run `scripts/new-niche.py`:

```bash
# 1. Clone this repository
git clone https://github.com/aammo1/ai-memory-boilerplate.git
cd ai-memory-boilerplate

# 2. Initialize your unified vault + install all 4 skills + clone & configure your first store!
python3 scripts/new-niche.py \
  --store "glow-skin" \
  --name "Your Name"
```

What `new-niche.py` does automatically:
1. **If `~/Work/ai-memory` does not exist yet:** Runs `setup.py` to initialize the unified Obsidian vault, installs all 4 skills (`ai-memory-kit`, `morocco-cod-marketing`, `crm-catalog`, `product-page-marketing-sections`) into `~/.agents/skills/`, and **auto-symlinks** them into any detected AI harness on your machine (`~/.claude/skills`, `~/.codex/skills`, `~/.gemini/config/skills` for Antigravity, `~/.cursor/skills`).
2. **Creates Product Pictures folders:** `~/Pictures/glow-skin_pics/staging/` and `uploaded/`.
3. **Clones & configures [`store-crm-boilerplate`](https://github.com/aammo1/store-crm-boilerplate):** Clones into `~/Projects/glow-skin`, runs `npm install` + `npm run new-store` (sharing `CATALOG_AGENT_KEY` across `.env.local` and `.env.production.example`), writes `~/.config/glow-skin/catalog-agent.env` + `catalog-agent.prod.env` (`chmod 600`), and links `~/Projects/glow-skin/AGENTS.md` to your vault.
4. **Wires real paths in `PROFILE.md`:** Updates `~/Work/ai-memory/PROFILE.md` with your real repository, production URL, pictures, and catalog env paths.

---

### Alternative: Initialize Vault Only (Without Cloning a Store Repo Yet)

```bash
python3 scripts/setup.py \
  --memory-dir "$HOME/Work/ai-memory" \
  --name "Your Name" \
  --stores "zehri,hellobaby" \
  --install-skill
```

What `setup.py` does:
- Creates `$HOME/Work/ai-memory` with `AGENTS.md`, `PROFILE.md`, `TODO.md`, and `LAUNCH-PIPELINE.md` pre-populated with your `--stores` columns.
- Scaffolds the marketing vault folders:
  - `00 Templates/Product Template.md`
  - `01 Products/<store>/` for each store
  - `02 Bases/Products_Marketing.base` (master table) + `02 Bases/<store>_Marketing.base` (per-store tables)
  - `03 Assets/Product images/` and `03 Assets/Reference Heroes/`
  - `.obsidian/` settings so Obsidian **Bases** and **Templates** work out of the box
- Copies `tools/kie_generate.py`, `tools/test_kie_generate.py`, and `scripts/new-niche.py` into `<vault>/tools/` (never overwrites existing files unless `--force` is passed).
- Initializes a Git repository inside `$HOME/Work/ai-memory`.
- Installs all 4 bundled skills (`ai-memory-kit`, `morocco-cod-marketing`, `crm-catalog`, `product-page-marketing-sections`) into `~/.agents/skills/` and auto-symlinks detected AI harnesses (`~/.claude/skills`, `~/.codex/skills`, `~/.gemini/config/skills`, `~/.cursor/skills`).
- After pulling updates to this repo, refresh installed skills anytime without touching your vault notes:
  ```bash
  python3 scripts/setup.py --memory-dir "$HOME/Work/ai-memory" --update-skills
  ```

### Adding a New Store or Niche Later (Via the Skill)

You never need to run `setup.py` again after initial setup. Just tell your AI from any folder:
- *"use `ai-memory-kit` and add a new store called `new-brand`"*

The `ai-memory-kit` skill automatically creates `01 Products/new-brand/`, creates `02 Bases/new-brand_Marketing.base`, adds a `new-brand Products` view tab to `02 Bases/Products_Marketing.base`, and appends the `new-brand` column to `PROFILE.md`.

### Health Check & Offline Tests

```bash
# Verify required files, marketing folders, YAML schema keys, cover image links, and secret leaks
python3 scripts/verify.py --memory-dir "$HOME/Work/ai-memory"

# Run offline unit tests for vault setup, harness symlinks & verification (6 tests)
python3 scripts/test_vault.py

# Run offline unit tests for the Kie.ai batch & recovery generator (14 tests, 0 API calls)
uv run --script tools/test_kie_generate.py
```

---

## 3 Ways to Use Your Unified Vault

### 1. On-Demand From Any Folder (Via the Skill)
Open **any** folder on your laptop in your AI tool and type:
- *"use `ai-memory-kit` and check my open tasks"*
- *"use `ai-memory-kit` and create a marketing plan for a new product under `01 Products/zehri/`"*
- *"use `ai-memory-kit` and onboard a new store called `cosmetics` into `PROFILE.md` and `01 Products/`"*

### 2. Automatic Per-Project Connection (No Symlinks)
If you want a specific store or project repository to load your unified vault automatically every time you open it, paste these 5 lines at the top of that project's local `AGENTS.md`:

```markdown
## External Memory & Workflow
Shared cross-session memory & marketing vault lives in ~/Work/ai-memory:
- System Map & Preferences: ~/Work/ai-memory/PROFILE.md
- Open Tasks & Log: ~/Work/ai-memory/TODO.md
- 10-Step Product Launch SOP: ~/Work/ai-memory/LAUNCH-PIPELINE.md
```

### 3. Direct Vault Management in Obsidian
Open `$HOME/Work/ai-memory` in **Obsidian**:
- Open `02 Bases/Products_Marketing.base` to view all products across every store/niche with cover images.
- Open `02 Bases/<store>_Marketing.base` to view a single store's product marketing table.
- Edit `00 Templates/Product Template.md` to customize discovery methods, categories, angles, emotions, hooks, or creative techniques for your specific niche.

---

## Customizing `LAUNCH-PIPELINE.md` for Your Domain

`templates/LAUNCH-PIPELINE.md.template` includes the complete **10-step E-Commerce Product Launch Pipeline (Steps 0 to 10)**:
- **Step 0 (Resume & State Check):** Reads a per-product `launch-state.json` under an exclusive `flock` lock so interrupted runs never repeat completed work.
- **Step 1 & 2 (Photos & Marketing Plan):** Creates `01 Products/<store>/<product_name>.md` directly inside the unified vault using `00 Templates/Product Template.md` and saves the cover image to `03 Assets/Product images/`.
- **Step 3 (Staging Folder Tree):** Standardized `staging/<product_name>/` + color variant subfolders + `ads_folder/`.
- **Steps 4, 5 & 6 (Kie.ai Gallery & Static Ads + Token-Saving Gate):** Uses `tools/kie_generate.py` and `03 Assets/Reference Heroes/<store>_hero_01.png` (supports single-image and `--batch` mode, input SHA-256 fingerprinting, `--adopt-task-id`, and `--retry-failed`) and always asks which specific gallery positions and ads to generate before spending API credits.
- **Steps 7, 8, 9 & 10 (Review Gate -> Catalog -> Landing Page Sections -> Paused Meta Ads Drafts):** Hard human approval stops before live catalog uploads, code changes, deployments, or ad creation.

---

## Repository Structure

```text
ai-memory-boilerplate/
├── README.md                                  # Documentation
├── LICENSE                                    # MIT License
├── scripts/
│   ├── new-niche.py                           # One-command launcher (vault + 4 skills + store-crm-boilerplate)
│   ├── setup.py                               # CLI installer (--stores, --add-store, --install-skill)
│   ├── verify.py                              # Health, frontmatter, cover-link & secret-leak checker
│   └── test_vault.py                          # Offline unit tests for setup.py, verify.py, and new-niche.py
├── skill/
│   ├── ai-memory-kit/                         # On-demand unified vault & pipeline skill
│   ├── morocco-cod-marketing/                 # Moroccan COD ad package & page-brief skill
│   ├── crm-catalog/                           # Live catalog API v2 skill for store-crm-boilerplate
│   └── product-page-marketing-sections/       # Mobile-first product-page marketing sections skill
├── templates/
│   ├── AGENTS.md.template                     # Unified vault boot instructions
│   ├── PROFILE.md.template                    # Identity, dynamic multi-store paths table, and AI rules
│   ├── TODO.md.template                       # Open tasks queue and recent completed log
│   ├── LAUNCH-PIPELINE.md.template            # Full 10-step product launch pipeline (Steps 0 to 10)
│   ├── Product Template.md.template           # Marketing note YAML schema & choice catalog for 00 Templates/
│   ├── Products_Marketing.base.template       # Obsidian Base table template for 02 Bases/
│   └── obsidian/plugins/good-bases/           # Bundled GoodBases (notion-table) Obsidian plugin
└── tools/
    ├── kie_generate.py                        # Crash-safe, batch-capable Kie.ai image generator
    └── test_kie_generate.py                   # 14 offline unit tests for recovery, locking, and batch mode
```

## License

MIT License — free for personal and commercial use.
