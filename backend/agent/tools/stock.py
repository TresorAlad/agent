import json

from agent.data_store import load_catalog, load_stock


def verifier_stock(*, product_id: str, quantite: int = 1) -> str:
    stock_rows = {row["product_id"]: row for row in load_stock()}
    catalog = {p["id"]: p for p in load_catalog()}

    if product_id not in catalog:
        return json.dumps(
            {"error": "Produit inconnu.", "product_id": product_id},
            ensure_ascii=False,
        )

    row = stock_rows.get(product_id, {"quantite": 0})
    available_qty = int(row.get("quantite", 0))
    product = catalog[product_id]
    available = available_qty >= quantite

    alternatives: list[dict] = []
    if not available:
        cat = product.get("categorie")
        for pid, p in catalog.items():
            if pid == product_id:
                continue
            if p.get("categorie") != cat:
                continue
            qty = int(stock_rows.get(pid, {}).get("quantite", 0))
            if qty > 0:
                alternatives.append(
                    {
                        "id": pid,
                        "nom": p["nom"],
                        "prix_xof": p["prix_xof"],
                        "stock_disponible": qty,
                    }
                )

    return json.dumps(
        {
            "product_id": product_id,
            "nom": product["nom"],
            "quantite_demandee": quantite,
            "stock_disponible": available_qty,
            "available": available,
            "alternatives": alternatives[:3],
        },
        ensure_ascii=False,
    )
