# Setup (`crm-catalog` — Contract v2)

## 1. Server Configuration (`store-crm-boilerplate`)

On the CRM server (or in `.env.local` / Coolify environment variables), set `CATALOG_AGENT_KEY` to a random secret of at least 32 characters:

```bash
openssl rand -hex 32
```

When `CATALOG_AGENT_KEY` is unset or shorter than 32 characters, `/api/catalog-agent` returns `503`. Note that `npm run new-store` automatically generates and shares the same `CATALOG_AGENT_KEY` across `.env.local` and `.env.production.example` (and `new-niche.py` writes both `catalog-agent.env` for local dev and `catalog-agent.prod.env` when a production `https://` URL is present).

## 2. Client Environment Files (`catalog-agent.env` local, `catalog-agent.prod.env` live)

Create a private environment file per store/niche outside the repository:

```bash
mkdir -p "$HOME/.config/<store>"
chmod 700 "$HOME/.config/<store>"
# live store example (for local dev use catalog-agent.env with http://localhost:3000)
cat > "$HOME/.config/<store>/catalog-agent.prod.env" << 'EOF'
CRM_CATALOG_URL=https://your-store-domain.ma
CRM_CATALOG_KEY=<same-32+-char-secret-as-CATALOG_AGENT_KEY>
EOF
chmod 600 "$HOME/.config/<store>/catalog-agent.prod.env"
```

Use one file per environment:

| File | `CRM_CATALOG_URL` | `CRM_CATALOG_KEY` |
|---|---|---|
| `~/.config/<store>/catalog-agent.env` | `http://localhost:3000` | `CATALOG_AGENT_KEY` from the repo's `.env.local` |
| `~/.config/<store>/catalog-agent.prod.env` | `https://<your-store-domain>` | `CATALOG_AGENT_KEY` set in Coolify / production env |

`new-niche.py` creates both automatically when the store has an `https://` domain. If you deployed later or changed the domain, create or fix `catalog-agent.prod.env` with the commands above, then add its path to the **Catalog API Env (Production)** row of `PROFILE.md`.

- `CRM_CATALOG_URL` must be an HTTPS origin without path, query, fragment, or credentials (`http://localhost:3000` and `http://127.0.0.1:3000` are also allowed for local testing).
- Test connectivity from any directory:

```bash
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" capabilities
# live store:
node --env-file="$HOME/.config/<store>/catalog-agent.prod.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" capabilities
```
