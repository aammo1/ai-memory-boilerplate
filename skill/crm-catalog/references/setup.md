# Setup (`crm-catalog` — Contract v2)

## 1. Server Configuration (`store-crm-boilerplate`)

On the CRM server (or in `.env.local` / Coolify environment variables), set `CATALOG_AGENT_KEY` to a random secret of at least 32 characters:

```bash
openssl rand -hex 32
```

When `CATALOG_AGENT_KEY` is unset or shorter than 32 characters, `/api/catalog-agent` returns `503`. Note that `npm run new-store` automatically generates `CATALOG_AGENT_KEY` in `.env.local` and `.env.production.example`.

## 2. Client Environment File (`~/.config/<store>/catalog-agent.env`)

Create a private environment file per store/niche outside the repository:

```bash
mkdir -p "$HOME/.config/<store>"
chmod 700 "$HOME/.config/<store>"
cat > "$HOME/.config/<store>/catalog-agent.env" << 'EOF'
CRM_CATALOG_URL=https://your-store-domain.ma
CRM_CATALOG_KEY=<same-32+-char-secret-as-CATALOG_AGENT_KEY>
EOF
chmod 600 "$HOME/.config/<store>/catalog-agent.env"
```

- `CRM_CATALOG_URL` must be an HTTPS origin without path, query, fragment, or credentials (`http://localhost:3000` and `http://127.0.0.1:3000` are also allowed for local testing).
- Test connectivity from any directory:

```bash
node --env-file="$HOME/.config/<store>/catalog-agent.env" "$HOME/.agents/skills/crm-catalog/scripts/catalog-agent-client.mjs" capabilities
```
