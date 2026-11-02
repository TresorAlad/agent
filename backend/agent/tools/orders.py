import json
import uuid
from datetime import datetime, timezone

from agent.data_store import load_catalog, load_orders, save_orders


def obtenir_statut_commande(*, order_id: str) -> str:
    orders = load_orders()
    for order in orders:
        if order.get("id") == order_id:
            return json.dumps(
                {
                    "id": order["id"],
                    "statut": order["statut"],
                    "total_xof": order.get("total_xof"),
                },
                ensure_ascii=False,
            )
    return json.dumps({"error": "Commande introuvable.", "order_id": order_id}, ensure_ascii=False)


def creer_commande(
    *,
    client_phone: str,
    lignes: list[dict],
    frais_livraison_xof: float,
    client_confirmed: bool = False,
    devise_affichee: str = "XOF",
) -> str:
    catalog = {p["id"]: p for p in load_catalog()}
    total_articles = 0.0
    normalized_lines: list[dict] = []

    for line in lignes:
        pid = line.get("product_id")
        qty = int(line.get("quantite", 1))
        if pid not in catalog:
            return json.dumps(
                {"error": f"Produit inconnu: {pid}"},
                ensure_ascii=False,
            )
        prix = float(catalog[pid]["prix_xof"])
        subtotal = prix * qty
        total_articles += subtotal
        normalized_lines.append(
            {
                "product_id": pid,
                "nom": catalog[pid]["nom"],
                "quantite": qty,
                "prix_unitaire_xof": prix,
                "sous_total_xof": subtotal,
            }
        )

    livraison = float(frais_livraison_xof)
    total = total_articles + livraison

    if not client_confirmed:
        statut = "pending_client"
    else:
        statut = "pending_manager"

    order_id = f"CMD-{uuid.uuid4().hex[:8].upper()}"
    order = {
        "id": order_id,
        "client_phone": client_phone,
        "lignes": normalized_lines,
        "livraison_xof": livraison,
        "total_xof": total,
        "devise_affichee": devise_affichee,
        "statut": statut,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    return json.dumps(
        {
            "id": order_id,
            "statut": statut,
            "total_xof": total,
            "livraison_xof": livraison,
            "message": (
                "Commande enregistrée, en attente de confirmation client."
                if statut == "pending_client"
                else "Commande en attente de validation par la gérante."
            ),
        },
        ensure_ascii=False,
    )
