---
name: crm-catalog
description: >-
  Manages any store-crm-boilerplate live catalog (Contract v2) through its
  authenticated /api/catalog-agent API. Creates, edits, archives, and restores
  products across any niche (cosmetics, apparel, gadgets, home, baby, footwear,
  single-SKU or multi-option up to 3 axes) with WebP galleries and opening stock.
  Use when adding, editing, archiving, or restoring products on a store built from
  store-crm-boilerplate (where the env file defines CRM_CATALOG_URL and
  CRM_CATALOG_KEY).
---

# Store CRM Live Catalog (Contract v2)

This skill ships a standalone client at `scripts/catalog-agent-client.mjs` **inside this skill's own folder** (default install: `$HOME/.agents/skills/crm-catalog/`; it may also be reached through a harness symlink such as `~/.claude/skills/crm-catalog/`). Resolve that absolute path once and call it `CLIENT` below. It runs with Node.js 22+ from any working directory and connects to any `store-crm-boilerplate` `/api/catalog-agent` endpoint (Contract v2); catalog changes take effect immediately and trigger `revalidateStorefront()` without a rebuild. Read `references/setup.md` if credentials or the API are unavailable, and `references/contract.md` when constructing requests.

```bash
CLIENT="$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs"   # adjust if this skill lives elsewhere
```

## Boundaries

- Manage products exclusively through this client—never mutate SQLite directly, run SQL, SSH into the container, or automate browser forms.
- Enter initial stock **only when creating a new product** (`initialStock: [{ variantKey, qty }]`). An edit cannot modify stock (`key` and `initialStock` are forbidden on edit). Direct the merchant to `/crm/stock` for subsequent inventory receipts or adjustments.
- Preserve order history, variant IDs/SKUs, and stock movements. “Delete/remove a product” means propose **archive**, explaining that it hides the product on the storefront while preserving historical order/return references.
- Storefront copy matches the target store's configured language (`fr` or `ar` from `store.config.ts`); prices are positive integer MAD.
- Never expose `CRM_CATALOG_KEY` or put it in operation JSON, command arguments, preview files, or Git. Always pass it via `--env-file` or environment variables.

## Workflow

Track these steps for each request:
- [ ] Choose the target store **and** environment (local or live) and confirm its origin.
- [ ] Discover live capabilities and identify the exact product (if editing/archiving).
- [ ] Gather missing facts and prepare copy, option axes, variants, and photos.
- [ ] Create a signed preview and explain the exact changes.
- [ ] Obtain the user's explicit approval of that specific preview.
- [ ] Apply, then verify and summarize the saved receipt and live product.

### 0. Choose the target environment (local vs. live)

Each store usually has two env files (paths listed in `PROFILE.md`):

| Env file | `CRM_CATALOG_URL` | Use for |
|---|---|---|
| `~/.config/<store>/catalog-agent.env` | `http://localhost:3000` | The copy running on this computer (`npm run dev`) |
| `~/.config/<store>/catalog-agent.prod.env` | `https://<store-domain>` | The deployed store that customers see |

- If both files exist and the user did not say which one, **ask "local or live store?"** before anything else. Never default silently: products created locally do not appear on the live site.
- If only the local file exists and the user wants the live store, stop and point them to `references/setup.md` §2 to create `catalog-agent.prod.env`.
- Read the chosen file's `CRM_CATALOG_URL` (never print the key) and state the target origin to the user. Set `ENV_FILE` to that path for every command below.
- A plan is bound to its origin: a preview prepared against local cannot be applied to live. Prepare a new preview for the other environment.

### 1. Discover

```bash
node --env-file="$ENV_FILE" "$CLIENT" capabilities
node --env-file="$ENV_FILE" "$CLIENT" list
node --env-file="$ENV_FILE" "$CLIENT" show <exact-id-or-slug>
```

Always check live `capabilities` (`schemaVersion: 2`) and current product state before drafting an operation. "Network request failed" against `http://localhost:3000` usually means the local dev server is not running.

### 2. Gather and prepare

**Creation (Niche-Agnostic Variants):**
- Obtain product name, category (free text matching the store's nav/categories), integer MAD price, photos, and option structure:
  - **Single-SKU / Optionless product** (e.g., a gadget, cream, or accessory with no options): use `variants: [{ "key": "standard", "options": [] }]` and `initialStock: [{ "variantKey": "standard", "qty": <n> }]`.
  - **1 to 3 Option Axes** (e.g., `Couleur`, `Taille`, `Contenance`, `Modèle`): define `optionDefinitions: [{ "name": "...", "values": ["..."] }]`, list each active combination in `variants: [{ "key": "<ascii_key>", "options": [{ "name": "...", "value": "..." }], "images": [...] }]`, and map opening stock in `initialStock: [{ "variantKey": "<ascii_key>", "qty": <n> }]`.
- Do not invent materials, dimensions, capacities, or performance claims. Ask for missing required facts and confirm opening stock quantities before previewing.

**Editing:**
- Send only changed fields (`target` is the exact product ID or slug).
- When modifying `variants` or `optionDefinitions`, provide the **complete desired active variant list**. Pass the existing persistent variant `id` (from `show` or the creation receipt) when changing a variant's options so historical orders and stock remain attached; otherwise canonical options match existing variants automatically.
- Omitted variants become inactive without deleting historical references. Newly created variants on edit start at 0 stock.

**Photos:**
- Accept JPG/PNG/WebP local files or HTTPS image URLs (up to 5 MB). Never include `ads_folder/` images in product or variant galleries.
- **Always write local photos as absolute paths** (e.g. `/home/me/Pictures/<store>_pics/staging/<product>/standard/01.png`). The client resolves relative paths against the folder of `operation.json`, not your working directory, so `./staging/...` breaks as soon as the JSON lives in a temp folder.
- Product-level images go in `data.images`; variant-specific galleries go in `data.variants[].images`.
- The client stages sources locally and computes dry-run WebP paths during `preview`; actual media uploads happen only during `apply`.

### 3. Preview and approve

Write operation JSON and plans to a private temp folder outside any repo (works on every harness and OS):

```bash
WORK="$(mktemp -d "${TMPDIR:-/tmp}/crm-catalog.XXXXXX")"
# write "$WORK/operation.json" (absolute image paths), then:
node --env-file="$ENV_FILE" "$CLIENT" preview "$WORK/operation.json" "$WORK/plan.json"
```

Keep `$WORK` until `apply` finishes: `plan.json.images/` holds the SHA-256-checked photo copies.

Present the **target origin (local or live URL)**, action, product name/slug, category, price, option definitions, variants, image galleries, initial stock per `variantKey`, and preview expiration (30 minutes). Wait for explicit user approval before running `apply`.

### 4. Apply and verify

Only after explicit user approval, and after restating the target origin one last time:

```bash
node --env-file="$ENV_FILE" "$CLIENT" apply "$WORK/plan.json" --yes
```

Compare the applied receipt (`variantIds` map, product ID, slug) with the current product returned by `apply`. If a request times out, check `node --env-file="$ENV_FILE" "$CLIENT" receipt <requestId>` before retrying the same plan. Report which environment was changed and the product URL on that origin (`<origin>/produit/<slug>`).
