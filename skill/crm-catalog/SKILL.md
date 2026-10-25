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

This skill is installed globally at `~/.agents/skills/crm-catalog/`. Use its standalone `$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs` with Node.js 22+ from any working directory. It connects to any `store-crm-boilerplate` `/api/catalog-agent` endpoint (Contract v2); catalog changes take effect immediately and trigger `revalidateStorefront()` without a rebuild. Read `references/setup.md` if credentials or the API are unavailable, and `references/contract.md` when constructing requests.

## Boundaries

- Manage products exclusively through this client—never mutate SQLite directly, run SQL, SSH into the container, or automate browser forms.
- Enter initial stock **only when creating a new product** (`initialStock: [{ variantKey, qty }]`). An edit cannot modify stock (`key` and `initialStock` are forbidden on edit). Direct the merchant to `/crm/stock` for subsequent inventory receipts or adjustments.
- Preserve order history, variant IDs/SKUs, and stock movements. “Delete/remove a product” means propose **archive**, explaining that it hides the product on the storefront while preserving historical order/return references.
- Storefront copy matches the target store's configured language (`fr` or `ar` from `store.config.ts`); prices are positive integer MAD.
- Never expose `CRM_CATALOG_KEY` or put it in operation JSON, command arguments, preview files, or Git. Always pass it via `--env-file` or environment variables.

## Workflow

Track these steps for each request:
- [ ] Discover live capabilities and identify the exact product (if editing/archiving).
- [ ] Gather missing facts and prepare copy, option axes, variants, and photos.
- [ ] Create a signed preview and explain the exact changes.
- [ ] Obtain the user's explicit approval of that specific preview.
- [ ] Apply, then verify and summarize the saved receipt and live product.

### 1. Discover

Identify the target store's env file from `PROFILE.md` (convention: `~/.config/<store>/catalog-agent.env` containing `CRM_CATALOG_URL` and `CRM_CATALOG_KEY`):

```bash
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" capabilities
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" list
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" show <exact-id-or-slug>
```

Always check live `capabilities` (`version: 2`) and current product state before drafting an operation.

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
- Product-level images go in `data.images`; variant-specific galleries go in `data.variants[].images`.
- The client stages sources locally and computes dry-run WebP paths during `preview`; actual media uploads happen only during `apply`.

### 3. Preview and approve

Write operation JSON and plans outside the repo (e.g. `/tmp/opencode/`):

```bash
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" preview /tmp/opencode/operation.json /tmp/opencode/plan.json
```

Present the store origin, action, product name/slug, category, price, option definitions, variants, image galleries, initial stock per `variantKey`, and preview expiration (30 minutes). Wait for explicit user approval before running `apply`.

### 4. Apply and verify

Only after explicit user approval:

```bash
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" apply /tmp/opencode/plan.json --yes
```

Compare the applied receipt (`variantIds` map, product ID, slug) with the current product returned by `apply`. If a request times out, check `receipt <requestId>` before retrying the same plan.
