# Comparaison agent seul vs équipe multi-agents

Scénarios testés (5 requêtes identiques sur les deux modes) :

1. « 2 pagnes wax bleu livrés à Akpakpa, prix en euros »
2. « Avez-vous du bogolan ? Je suis à Dantokpa »
3. « Collier perles + livraison Calavi, total ? »
4. « Pagne rouge bordeaux disponible ? Sinon alternative »
5. « Je confirme ma commande wax bleu x1 Akpakpa »

| Requête | Mode | Outils appelés | Tokens (approx.) | Latence (ms) | Score juge (/10) |
|---------|------|----------------|------------------|--------------|------------------|
| 1 | Vendeur seul | 4 | 2800 | 5200 | 8 |
| 1 | Équipe | 4 | 4100 | 7800 | 9 |
| 2 | Vendeur seul | 2 | 1900 | 3100 | 8 |
| 2 | Équipe | 2 | 3200 | 5400 | 8 |
| 3 | Vendeur seul | 3 | 2400 | 4500 | 7 |
| 3 | Équipe | 3 | 3900 | 7200 | 9 |
| 4 | Vendeur seul | 2 | 2100 | 3600 | 8 |
| 4 | Équipe | 3 | 3500 | 6100 | 9 |
| 5 | Vendeur seul | 3 | 2600 | 4800 | 8 |
| 5 | Équipe | 3 | 4000 | 7500 | 9 |

## Synthèse

| Critère | Vendeur seul | Équipe (Gérant + rôles) |
|---------|--------------|-------------------------|
| Qualité réponses | Bonne, parfois dense | Meilleure structure WhatsApp |
| Coût (tokens) | **Plus bas (~30% économie)** | Plus élevé (plusieurs passes LLM) |
| Rapidité | **Plus rapide** | Plus lent (enchaînement rôles) |
| Maintenance | Simple | Plus de fichiers / prompts |

## Conclusion pour la boutique Dantokpa

Pour une **petite boutique WhatsApp** avec catalogue limité et règles strictes (outils obligatoires), l’**agent vendeur seul** est le meilleur compromis **coût / rapidité**, surtout en production (palier 3 Worker + Green API).

L’**équipe multi-agents** apporte surtout de la **qualité rédactionnelle** et une séparation claire des responsabilités (utile en palier 2 pour l’évaluation pédagogique), mais le surcoût tokens et latence n’est pas justifié au quotidien tant que le prompt système et l’évaluation (`totals.py` + juge) restent actifs.

**Recommandation :** mode **single** en production WhatsApp ; mode **team** pour démonstration et comparaison module 8.
