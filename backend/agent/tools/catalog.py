import json

from agent.data_store import load_catalog


def chercher_produit(*, query: str, limit: int = 5) -> str:
    q = query.lower().strip()
    if not q:
        return json.dumps({"error": "Requête vide.", "produits": []}, ensure_ascii=False)

    catalog = load_catalog()
    scored: list[tuple[int, dict]] = []

    for product in catalog:
        score = 0
        haystack = " ".join(
            [
                product.get("nom", ""),
                product.get("description", ""),
                " ".join(product.get("mots_cles", [])),
                product.get("categorie", ""),
            ]
        ).lower()
        for token in q.split():
            if token in haystack:
                score += 2
            if token in product.get("nom", "").lower():
                score += 3
        if score > 0:
            scored.append((score, product))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for _, p in scored[:limit]]

    return json.dumps(
        {
            "query": query,
            "count": len(results),
            "produits": [
                {
                    "id": p["id"],
                    "nom": p["nom"],
                    "description": p["description"],
                    "prix_xof": p["prix_xof"],
                    "categorie": p["categorie"],
                }
                for p in results
            ],
        },
        ensure_ascii=False,
    )
