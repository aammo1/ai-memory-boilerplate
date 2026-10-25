# Setup Guide: New User + New Store (`ai-memory-boilerplate` + `store-crm-boilerplate`)

Complete setup on a **new computer, for a new user, with a new store**. The example store slug is **`glow-skin`**; replace it with your own.

**Who this is for:** Moroccan cash-on-delivery (COD) sellers who are comfortable running a few terminal commands. The store uses MAD prices, Moroccan `+212` phone numbers, Ozon Express (or a mock courier), a French CRM and a `fr` or `ar` storefront.

---

## 0. Prerequisites

**Required**
- **OS:** Linux, macOS, or Windows **WSL2** (`kie_generate.py` uses Unix `fcntl.flock`).
- **Python 3.11+** and **`uv`**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js 22+** and **npm**. If `npm install` fails on `better-sqlite3`, install C++ build tools (`build-essential` + `python3` on Linux, Xcode Command Line Tools on macOS).
- **Git** and a **GitHub** account (for private backups).
- **Obsidian 1.10.2+** (needed for Obsidian Bases and the bundled GoodBases plugin).
- **An AI coding tool:** Claude Code, Codex, OpenCode, Cursor, Antigravity, or similar.

**Optional (only for some pipeline steps)**
- **Kie.ai API key:** AI gallery and ad images (pipeline Steps 4–6).
- **Meta Ads MCP server** configured in your AI tool: paused Meta ad drafts (Step 10).
- **Coolify server + domain:** to put the store online (Step 6 below).

---

## 1. Clone `ai-memory-boilerplate`

```bash
git clone https://github.com/aammo1/ai-memory-boilerplate.git
cd ai-memory-boilerplate
```

Keep this folder: you will run `scripts/verify.py` and future updates from it. You do **not** need to clone `store-crm-boilerplate` yourself; the next step does it.

---

## 2. Run the one-command launcher

```bash
python3 scripts/new-niche.py --store "glow-skin" --name "Your Name"
```

It does four things:

1. **Creates your Obsidian vault** at `~/Work/ai-memory`: `AGENTS.md`, `PROFILE.md`, `TODO.md`, `LAUNCH-PIPELINE.md`, `00 Templates/`, `01 Products/glow-skin/`, `02 Bases/` tables and `03 Assets/`.
2. **Installs the 4 AI skills** into `~/.agents/skills/` and links them automatically into every AI tool it finds: `~/.claude/skills`, `~/.codex/skills`, `~/.cursor/skills`, `~/.gemini/config/skills` (Antigravity app/IDE) and `~/.gemini/antigravity-cli/skills`. OpenCode and Gemini CLI read `~/.agents/skills` directly. You don't need to configure anything.
   - `ai-memory-kit`: loads your memory, tracks tasks, and adds new stores from any folder.
   - `morocco-cod-marketing`: COD strategy, 6 static ads, optional video scripts, and a product-page brief.
   - `crm-catalog`: creates and edits products, variants, opening stock, packs and landing pages in your store.
   - `product-page-marketing-sections`: custom mobile-first product-page sections (`src/custom/`).
   - If you see `WARNING: ... is a real folder`, an older copy of that skill already exists there. Move it away and run the update command in section 9.
3. **Creates your store + CRM** at `~/Projects/glow-skin`: clones `store-crm-boilerplate`, runs `npm install`, then the French store wizard (`npm run new-store`). Wizard tips:
   - **Slug:** already set to `glow-skin`. Keep it, so the vault, config folder and store all use the same name.
   - **Domaine:** enter your **real future domain** (for example `https://glow-skin.ma`), even if the site is not online yet. If you enter `http://localhost:3000`, the live catalog file in point 4 is not created.
   - **WhatsApp:** Moroccan mobile number (`06…`, `07…`, `+2126…` or `2126…`).
   - **Admin email + password:** 12–128 characters, typed twice (hidden while typing). Write them down: this is your CRM login.
   - **Non-interactive mode:** `--answers path/to/answers.json` (copy `examples/new-store-answers.json` from the store repo). Leave `"adminPassword": ""` to get a random password, **printed once**. Save it right away.
4. **Connects everything:**
   - Creates `~/Pictures/glow-skin_pics/staging/` and `uploaded/`.
   - Writes two private catalog files (`chmod 600`):

     | File | Points to | Used when |
     |---|---|---|
     | `~/.config/glow-skin/catalog-agent.env` | `http://localhost:3000` | You test on your own computer |
     | `~/.config/glow-skin/catalog-agent.prod.env` | `https://glow-skin.ma` | You add products to the **real** store customers see |

   - Adds a link to your vault at the top of `~/Projects/glow-skin/AGENTS.md`.
   - Writes all real paths (including both catalog files) into `~/Work/ai-memory/PROFILE.md`.

---

## 3. First login (local)

```bash
cd ~/Projects/glow-skin
npm run dev
```

1. Open `http://localhost:3000`: your storefront (empty until you add products).
2. Open `http://localhost:3000/login` and sign in with the admin email and password from the wizard.
3. You land in the CRM (`/crm`). The product catalog is at `/admin`.

Forgot the password? Run this from `~/Projects/glow-skin`:

```bash
node scripts/create-user.mjs you@example.com '<new-password-12-chars-min>' 'Admin' admin
```

---

## 4. Open the vault in Obsidian

1. Obsidian → **Open folder as vault** → `~/Work/ai-memory`.
2. When asked, click **Trust author and enable plugins** so GoodBases loads.
3. Open `02 Bases/Products_Marketing.base` to see the products of all your stores (empty at first).
4. Check the vault's health at any time, from the `ai-memory-boilerplate` folder:

   ```bash
   python3 scripts/verify.py --memory-dir ~/Work/ai-memory
   ```

---

## 5. Optional: Kie.ai key and hero style image

**Kie.ai key** (only for AI images). Don't use `echo`: it saves the key in your shell history.

```bash
mkdir -p ~/.config/kie && chmod 700 ~/.config/kie
printf "Paste your Kie.ai key: "; read -rs K && printf 'KIE_API_KEY=%s\n' "$K" > ~/.config/kie/kie.env && unset K && echo
chmod 600 ~/.config/kie/kie.env
```

**Hero style image (optional):** if you already have a main photo in your store's style, save it as `~/Work/ai-memory/03 Assets/Reference Heroes/glow-skin_hero_01.png`. If not, skip this: on your first product, the pipeline generates a hero without a reference, and once you approve it, saves it here for all future products.

---

## 6. Back up and deploy

**Private backups (recommended now).** Neither repository has a remote yet. Create two **private** GitHub repos, then:

```bash
cd ~/Projects/glow-skin
git add -A && git commit -m "Initial store"
git remote add origin git@github.com:<you>/glow-skin.git && git push -u origin main

cd ~/Work/ai-memory
git add -A && git commit -m "Initial vault"
git remote add origin git@github.com:<you>/ai-memory.git && git push -u origin main
```

Secrets (`.env.local`, `.env.production.example`) and the local database (`data/`) are git-ignored. Never commit, paste or share them.

> If `git push` complains about `main` vs `master`, run `git branch -M main` first.

**Deploy to Coolify** (full guide: `docs/new-niche.md` in the store repo, section 8):

1. New resource from your GitHub repo, build pack **Dockerfile**, port **3000**, **one replica** only.
2. Persistent volume on **`/app/data`** (database, photos, backups).
3. Environment variables: paste `~/Projects/glow-skin/.env.production.example`, then set **either** `SECURITY_TRUSTED_IP_HEADER="x-forwarded-for"` (only behind a proxy you control) **or** `SECURITY_ACCEPT_GLOBAL_BUDGETS="1"`. Without one of them the app refuses to start.
4. Health check: `/api/health`.
5. The live database starts **empty**: create your admin inside the container (Coolify → Terminal):

   ```bash
   node scripts/create-user.mjs you@example.com '<password-12-chars-min>' 'Admin' admin
   ```

**Live catalog file.** Keep `catalog-agent.env` as it is (local). The live store uses `~/.config/glow-skin/catalog-agent.prod.env`:
- **Already exists** if you entered an `https://` domain in the wizard. Check that its `CRM_CATALOG_URL` matches your real domain.
- **Missing, or your domain changed:** create or fix it with your domain and the `CATALOG_AGENT_KEY` value from Coolify:

  ```bash
  mkdir -p ~/.config/glow-skin && chmod 700 ~/.config/glow-skin
  printf "CATALOG_AGENT_KEY from Coolify: "; read -rs K && printf 'CRM_CATALOG_URL=https://glow-skin.ma\nCRM_CATALOG_KEY=%s\n' "$K" > ~/.config/glow-skin/catalog-agent.prod.env && unset K && echo
  chmod 600 ~/.config/glow-skin/catalog-agent.prod.env
  ```

  Then put its path in the **Catalog API Env (Production)** row of `~/Work/ai-memory/PROFILE.md`.

When you add products, the AI always asks **"local or live store?"** and shows the target URL before applying. Products created locally don't appear on the live site.

---

## 7. Daily workflow: launch a product

Open your AI tool in **any folder** and say:

> *"Use `ai-memory-kit` and launch this new product for `glow-skin`."*

The AI walks you through `LAUNCH-PIPELINE.md`, stopping for your approval at each important point:

- **Steps 1–2:** strategy and ad package in `01 Products/glow-skin/<PRODUCT>.md` (`morocco-cod-marketing`).
- **Step 3:** staging folders (`standard/` or one folder per variant, plus `ads_folder/`) in `~/Pictures/glow-skin_pics/staging/`.
- **Steps 4–6:** AI images with `kie_generate.py` (needs the Kie.ai key). It always asks which images to generate before spending credits.
- **Step 7:** you review everything (hard stop).
- **Step 8:** product upload with `crm-catalog` (local or live, preview → your approval → apply), including opening stock, packs and the `/l/<slug>` landing page.
- **Step 9:** custom product-page sections in `src/custom/` with `product-page-marketing-sections`, checked with lint, typecheck, build and `npm run perf-budget`.
- **Step 10:** paused Meta ad drafts (needs the Meta Ads MCP). Nothing is ever activated automatically.

Other useful prompts:
- *"Use `ai-memory-kit` and show my open tasks."*
- *"Use `crm-catalog` and change the price of `<product>` on the live store to 249 MAD."*

---

## 8. Add a second store later

From the **`ai-memory-boilerplate`** folder (after `git pull`, so you run the latest launcher):

```bash
git pull
python3 scripts/new-niche.py --store "car-gadgets"
```

Or ask your AI: *"Use `ai-memory-kit` and create a new store called `car-gadgets`."* It runs `~/Work/ai-memory/tools/new-niche.py`, which section 9 keeps up to date.

---

## 9. Update to the latest version

```bash
cd ai-memory-boilerplate
git pull
python3 scripts/setup.py --memory-dir ~/Work/ai-memory --update-skills
```

This refreshes:
- The 4 skills in `~/.agents/skills/` and their links in your AI tools. **Warning:** any edits you made directly in the installed skill files are overwritten. Keep your customizations in your own fork of this repo instead.
- `~/Work/ai-memory/tools/` (`kie_generate.py`, `new-niche.py`, tests). If you changed one of those files, your version is kept as `<file>.bak`.

Your notes (`PROFILE.md`, `TODO.md`, `01 Products/`, and so on) are never touched.

Each store is an **independent copy**: it does not receive `store-crm-boilerplate` updates automatically. See `docs/template-upgrades.md` in the store repo.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `npm install` fails on `better-sqlite3` | Install C++ build tools (see section 0) and use Node 22+. |
| AI says "Network request failed" on the local store | Run `npm run dev` in `~/Projects/glow-skin` first. |
| Catalog API returns `503` | `CATALOG_AGENT_KEY` is missing or shorter than 32 characters on that server. |
| Product added but not visible on the live site | It was added to the **local** store. Ask again for the **live** store (`catalog-agent.prod.env`). |
| Obsidian tables look plain | Enable community plugins (Settings → Community plugins) and turn on GoodBases. |
| Coolify container won't start | Set `SECURITY_TRUSTED_IP_HEADER` or `SECURITY_ACCEPT_GLOBAL_BUDGETS="1"`. |
| Skill not found in your AI tool | Run the update in section 9 and check for `WARNING` lines about real folders. |
