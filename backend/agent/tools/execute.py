import json
from typing import Any

from agent.tools import catalog, delivery, orders, stock
from agent.tools import currency as currency_tool


async def execute_tool(*, name: str, arguments: dict[str, Any]) -> str:
    if name == "chercher_produit":
        return catalog.chercher_produit(
            query=str(arguments.get("query", "")),
            limit=int(arguments.get("limit", 5)),
        )
    if name == "verifier_stock":
        return stock.verifier_stock(
            product_id=str(arguments.get("product_id", "")),
            quantite=int(arguments.get("quantite", 1)),
        )
    if name == "calculer_livraison":
        return delivery.calculer_livraison(
            zone=str(arguments.get("zone", "")),
            poids_kg=float(arguments.get("poids_kg", 1.0)),
        )
    if name == "convertir_devise":
        return await currency_tool.convertir_devise(
            montant_xof=float(arguments.get("montant_xof", 0)),
            devise_cible=str(arguments.get("devise_cible", "EUR")),
        )
    if name == "creer_commande":
        raw_lines = arguments.get("lignes") or []
        return orders.creer_commande(
            client_phone=str(arguments.get("client_phone", "client-demo")),
            lignes=raw_lines if isinstance(raw_lines, list) else [],
            frais_livraison_xof=float(arguments.get("frais_livraison_xof", 0)),
            client_confirmed=bool(arguments.get("client_confirmed", False)),
            devise_affichee=str(arguments.get("devise_affichee", "XOF")),
        )
    if name == "obtenir_statut_commande":
        return orders.obtenir_statut_commande(order_id=str(arguments.get("order_id", "")))

    return json.dumps({"error": f"Outil inconnu: {name}"}, ensure_ascii=False)
