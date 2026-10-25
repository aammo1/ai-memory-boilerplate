# Catalog Operation Contract (v2 — `store-crm-boilerplate`)

## Discovery

- `capabilities` returns `{ version: 2, ... }` with supported operations and schema rules.
- `list` returns all active and archived products with their `optionDefinitions`, `variants`, galleries, and availability.
- `show <id-or-slug>` returns one exact product.

## 1. Create (`command: "create"`)

### Optionless / Single-SKU Product (e.g., Gadget, Supplement, Book)

```json
{
  "command": "create",
  "requestId": "create-diffuseur-001",
  "data": {
    "name": "Diffuseur Ultrasonique",
    "slug": "diffuseur-ultrasonique",
    "category": "maison",
    "price": 249,
    "description": "Un diffuseur compact pour parfumer votre intérieur.",
    "images": ["./staging/DIFFUSEUR/standard/01.png", "./staging/DIFFUSEUR/standard/02.png"],
    "variants": [
      { "key": "standard", "options": [] }
    ],
    "initialStock": [
      { "variantKey": "standard", "qty": 15 }
    ]
  }
}
```

### Multi-Option Product (1 to 3 Axes — e.g., Cosmetics, Apparel, Footwear)

```json
{
  "command": "create",
  "requestId": "create-serum-001",
  "data": {
    "name": "Sérum Éclat",
    "slug": "serum-eclat",
    "category": "soins",
    "price": 199,
    "description": "Soin quotidien visage.",
    "images": ["./staging/SERUM/30ml/01.png"],
    "optionDefinitions": [
      { "name": "Contenance", "values": ["30 ml", "50 ml"] }
    ],
    "variants": [
      {
        "key": "30ml",
        "options": [{ "name": "Contenance", "value": "30 ml" }],
        "images": ["./staging/SERUM/30ml/01.png", "./staging/SERUM/30ml/02.png"]
      },
      {
        "key": "50ml",
        "options": [{ "name": "Contenance", "value": "50 ml" }],
        "images": ["./staging/SERUM/50ml/01.png"]
      }
    ],
    "initialStock": [
      { "variantKey": "30ml", "qty": 10 },
      { "variantKey": "50ml", "qty": 5 }
    ]
  }
}
```

### Creation Rules
- `data.variants[].key` is required when `variants` is provided: 1–100 ASCII alphanumeric, `_`, or `-` characters, unique within the request. `id` is forbidden on creation.
- `data.initialStock` accepts only `{ variantKey, qty }`. Every `variantKey` must match a declared variant `key`. Quantities are non-negative safe integers opened at location `MAIN` inside the creation transaction.
- Preview and applied receipts return `variantIds: { [key]: serverVariantId }`. Only the applied receipt contains persistent database variant IDs.
- Option values are always strings (including `"36"`, `"XL"`, `"500 ml"`). Up to 3 option axes and 100 variants per product.

## 2. Edit (`command: "edit"`)

```json
{
  "command": "edit",
  "requestId": "edit-serum-001",
  "target": "serum-eclat",
  "data": {
    "price": 219,
    "description": "Nouveau texte approuvé.",
    "optionDefinitions": [
      { "name": "Contenance", "values": ["30 ml", "50 ml", "100 ml"] }
    ],
    "variants": [
      { "id": "<persistent-id-from-show-or-receipt>", "options": [{ "name": "Contenance", "value": "30 ml" }] },
      { "id": "<persistent-id-from-show-or-receipt>", "options": [{ "name": "Contenance", "value": "50 ml" }] },
      { "options": [{ "name": "Contenance", "value": "100 ml" }] }
    ]
  }
}
```

### Edit Rules
- `key` and `initialStock` are forbidden on edit. All post-creation stock changes happen in `/crm/stock`.
- When `variants` is provided on edit, it represents the full final active selection. Omitted existing variants become inactive (`active: false`) without losing historical references. New variants start with `0` stock.

## 3. Archive & Restore (`command: "archive" | "restore"`)

```json
{
  "command": "archive",
  "requestId": "archive-serum-001",
  "target": "serum-eclat"
}
```

Use `"restore"` to unarchive. Neither operation alters stock or historical orders.
