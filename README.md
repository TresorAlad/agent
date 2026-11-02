# Boutique intelligente - Vendeur WhatsApp (Dantokpa)

Module 8 - Agent IA boutique (pagnes et accessoires, marché Dantokpa).

## Livrable module 8

| Élément | Emplacement |
|---------|-------------|
| README | Ce fichier |
| Trace (>= 3 étapes) | [`docs/trace-demo-reelle.json`](docs/trace-demo-reelle.json) (10 étapes, 4 outils) |
| Tableau comparatif | [`docs/comparaison-agents.md`](docs/comparaison-agents.md) |
| URL Worker (palier 3) | Nom Worker : `boutique-dantokpa` - URL affichée par `wrangler deploy` (voir [Palier 3](#palier-3---worker-cloudflare--whatsapp)) |
| Captures WhatsApp | [`docs/captures/client-commande.jpg`](docs/captures/client-commande.jpg), [`docs/captures/gerante-validation.jpg`](docs/captures/gerante-validation.jpg) |

### Extrait de trace (palier 1)

Enchaînement automatique sur une seule demande client :

1. `chercher_produit` (wax bleu)
2. `verifier_stock` (x2)
3. `calculer_livraison` (Akpakpa)
4. `convertir_devise` (EUR)

Trace complète : [`docs/trace-demo-reelle.json`](docs/trace-demo-reelle.json).

### Comparaison agent seul vs équipe (palier 2)

Voir le tableau détaillé dans [`docs/comparaison-agents.md`](docs/comparaison-agents.md).

**Conclusion :** pour cette boutique, l'agent **vendeur seul** est préférable en production (coût et latence), l'**équipe** reste utile pour la qualité rédactionnelle en démo.

---

## Structure

- `backend/` : Flask, agent tool-calling RodiumAI, multi-agents, évaluation
- `frontend/` : React (Vite) simulation WhatsApp + trace + validation gérante
- `worker/` : Cloudflare Worker + Green API (palier 3)
- `docs/` : trace, comparaison, captures

## Règles métier

- Aucun chiffre inventé : prix, stock, livraison, taux via outils uniquement
- Rupture : annoncée + alternatives proposées par `verifier_stock`
- Total = articles + livraison
- Commande : accord client **et** validation gérante

## Installation (paliers 1-2)

### Backend

```bash
cd backend
uv sync
cp .env.example .env
uv run python app.py
```

API : http://127.0.0.1:5000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI : http://127.0.0.1:5173 (proxy `/api` vers Flask)

### Démo trace

```bash
cd backend
uv run python ../scripts/demo_trace.py
```

## Palier 3 - Worker Cloudflare + WhatsApp

**Nom Worker** : `boutique-dantokpa` ([`worker/wrangler.toml`](worker/wrangler.toml))

Après `npm run deploy` dans `worker/` :

- **URL Worker** : `https://boutique-dantokpa.<votre-compte>.workers.dev`
- **Health** : `GET /health`
- **Webhook Green API** : `POST .../webhook`

Exemple (à remplacer par l'URL affichée par Wrangler) :

```text
https://boutique-dantokpa.<votre-compte>.workers.dev
```

### Captures WhatsApp

| Fichier | Description |
|---------|-------------|
| [client-commande.jpg](docs/captures/client-commande.jpg) | Conversation client / vendeur IA |
| [gerante-validation.jpg](docs/captures/gerante-validation.jpg) | Validation gérante OUI/NON |

### Déploiement

```bash
cd worker
npm install
npx wrangler login
npx wrangler kv namespace create BOUTIQUE_KV
# Copier l'id KV dans wrangler.toml
npx wrangler secret put RODIUMAI_API_KEY
npx wrangler secret put GREEN_API_ID
npx wrangler secret put GREEN_API_TOKEN
npx wrangler secret put MANAGER_PHONE
npm run deploy
```

Secrets locaux : `worker/.dev.vars.example` (ne pas committer `.dev.vars`).

Green API : webhook entrant vers `/webhook`. Gérante : `OUI CMD-XXXXXXXX` ou `NON CMD-XXXXXXXX`.

## Variables d'environnement

| Variable | Usage |
|----------|--------|
| `RODIUMAI_API_KEY` | LLM |
| `GREEN_API_URL`, `GREEN_API_ID`, `GREEN_API_TOKEN` | Green API |
| `MANAGER_PHONE` | Numéro gérante (E.164) |

Ne jamais committer `.env` ni `.dev.vars`.
