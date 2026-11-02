# Boutique intelligente - Vendeur WhatsApp (Dantokpa)

Agent conversationnel pour une boutique de pagnes et d'accessoires au marché Dantokpa (Cotonou, Bénin). Il répond aux clients, interroge le stock et le catalogue via des outils, calcule la livraison, convertit les devises et enregistre les commandes après accord du client et validation de la gérante.

**Dépôt :** https://github.com/TresorAlad/agent  
**Production (WhatsApp) :** https://boutique-dantokpa.bernardalade92.workers.dev

---

## Vue d'ensemble

| Composant | Rôle |
|-----------|------|
| [`backend/`](backend/) | API Flask, agent RodiumAI (tool calling), évaluation, mode multi-agents |
| [`frontend/`](frontend/) | Interface de démonstration (chat, trace des outils, validation gérante) |
| [`worker/`](worker/) | Cloudflare Worker + webhook Green API pour WhatsApp en production |
| [`docs/`](docs/) | Trace d'exécution, comparaison des architectures, captures d'écran |

### Règles métier

- Aucun prix, stock, délai ou total inventé : uniquement les résultats des outils.
- En cas de rupture : information claire et alternatives proposées par l'outil stock.
- Total commande = somme des articles + frais de livraison.
- Aucune commande finalisée sans accord explicite du client **et** validation de la gérante.

---

## Démarrage local (développement et démo)

### Prérequis

- Python 3.11+, [uv](https://github.com/astral-sh/uv)
- Node.js 18+ et npm
- Clé API RodiumAI (voir [`backend/.env.example`](backend/.env.example))

### Backend

```bash
cd backend
uv sync
cp .env.example .env
# Renseigner RODIUMAI_API_KEY dans .env
uv run python app.py
```

Contrôle : http://127.0.0.1:5000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Interface : http://127.0.0.1:5173 (les requêtes `/api` sont proxifiées vers Flask).

Les commandes passées sur **WhatsApp** sont stockées sur le Worker ; le panneau « Validation gérante » de l'interface les affiche aussi (synchronisation via `WORKER_URL` dans `.env`).

---

## Agent et outils

Cinq outils exposés au modèle :

| Outil | Fonction |
|-------|----------|
| `chercher_produit` | Recherche dans le catalogue JSON |
| `verifier_stock` | Disponibilité et alternatives en rupture |
| `calculer_livraison` | Tarifs par zone (Dantokpa, Cotonou, etc.) |
| `convertir_devise` | Conversion XOF via [Frankfurter](https://www.frankfurter.app/) |
| `creer_commande` | Enregistrement avec statuts (`pending_client`, `pending_manager`, `confirmed`) |

Limite de boucle : **6** tours d'appels d'outils ([`backend/config.py`](backend/config.py)).

### Trace d'exécution (agent simple)

Exemple réel : une demande client enchaîne **quatre outils** (`chercher_produit`, `verifier_stock`, `calculer_livraison`, `convertir_devise`).

- Trace complète : [`docs/trace-demo-reelle.json`](docs/trace-demo-reelle.json)
- Script de reproduction : `cd backend && uv run python ../scripts/demo_trace.py`

### Fiabilisation et multi-agents

- **Évaluation** avant réponse : contrôle arithmétique du total ([`backend/agent/evaluation/totals.py`](backend/agent/evaluation/totals.py)) et juge LLM ([`judge.py`](backend/agent/evaluation/judge.py)).
- **Mode équipe** : Gérant, Vendeur, Logisticien, Rédacteur (paramètre `mode=team` sur `/chat` ou bascule dans l'UI).
- **Comparaison** agent seul vs équipe (qualité, coût, latence) : [`docs/comparaison-agents.md`](docs/comparaison-agents.md).

---

## Production WhatsApp (Cloudflare + Green API)

| Élément | Valeur |
|---------|--------|
| URL du Worker | https://boutique-dantokpa.bernardalade92.workers.dev |
| Santé | https://boutique-dantokpa.bernardalade92.workers.dev/health |
| Webhook entrant (Green API) | `POST https://boutique-dantokpa.bernardalade92.workers.dev/webhook` |

Flux : message WhatsApp → Green API → Worker → agent + KV → réponse via Green API. Anti-doublon sur les webhooks, mémoire de conversation par fil, notification client après approbation de la gérante.

Validation gérante :

- **WhatsApp :** répondre `OUI CMD-XXXXXXXX` ou `NON CMD-XXXXXXXX` depuis le numéro configuré (`MANAGER_PHONE`).
- **Interface web :** panneau « Validation gérante » sur http://127.0.0.1:5173 (commandes Worker incluses).

### Déploiement du Worker

```bash
cd worker
npm install
npx wrangler login
npx wrangler kv namespace create BOUTIQUE_KV
# Reporter l'id KV dans wrangler.toml
npx wrangler secret put RODIUMAI_API_KEY
npx wrangler secret put GREEN_API_ID
npx wrangler secret put GREEN_API_TOKEN
npx wrangler secret put MANAGER_PHONE
npm run deploy
```

Modèle local : [`worker/.dev.vars.example`](worker/.dev.vars.example). Ne pas committer `.dev.vars` ni `backend/.env`.

---

## Pièces justificatives (évaluation)

| Document | Description |
|----------|-------------|
| [`docs/trace-demo-reelle.json`](docs/trace-demo-reelle.json) | Trace structurée (≥ 3 étapes, 4 appels d'outils sur un scénario) |
| [`docs/comparaison-agents.md`](docs/comparaison-agents.md) | Tableau comparatif vendeur seul vs équipe |
| [`docs/captures/client-commande.png`](docs/captures/client-commande.png) | Conversation WhatsApp client (commande, totaux) |
| [`docs/captures/gerante-validation.png`](docs/captures/gerante-validation.png) | Confirmation gérante envoyée au client |
| [`docs/captures/validation-gerante-ui.png`](docs/captures/validation-gerante-ui.png) | Interface React de validation (complément) |

Index des captures : [`docs/captures/README.md`](docs/captures/README.md).

---

## Variables d'environnement

| Variable | Fichier | Usage |
|----------|---------|--------|
| `RODIUMAI_API_KEY` | `backend/.env`, secrets Worker | API LLM |
| `RODIUMAI_MODEL` | idem | Modèle (défaut : `openai/gpt-4o-mini`) |
| `WORKER_URL` | `backend/.env` | Synchronisation des commandes WhatsApp vers l'UI |
| `GREEN_API_URL`, `GREEN_API_ID`, `GREEN_API_TOKEN` | Worker | Passerelle WhatsApp |
| `MANAGER_PHONE` | Worker | Numéro gérante (format international, ex. `22897050981`) |

---

## Licence et auteur

Projet réalisé dans le cadre d'un exercice sur les agents IA et le tool calling.  
Contact dépôt : [TresorAlad/agent](https://github.com/TresorAlad/agent).
