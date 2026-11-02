import json
import re
from typing import Any


def _parse_tool_payloads(trace_steps: list[dict]) -> dict[str, Any]:
    delivery_xof: float | None = None
    order_total: float | None = None
    article_totals: list[float] = []

    for step in trace_steps:
        if step.get("kind") != "tool_result":
            continue
        tool = step.get("tool")
        raw = step.get("result_summary") or ""
        try:
            data = json.loads(raw) if raw.startswith("{") else {}
        except json.JSONDecodeError:
            continue

        if tool == "calculer_livraison" and "frais_livraison_xof" in data:
            delivery_xof = float(data["frais_livraison_xof"])
        if tool == "creer_commande" and "total_xof" in data:
            order_total = float(data["total_xof"])
        if tool == "chercher_produit":
            for p in data.get("produits") or []:
                if "prix_xof" in p:
                    article_totals.append(float(p["prix_xof"]))

    return {
        "delivery_xof": delivery_xof,
        "order_total": order_total,
        "article_prices": article_totals,
    }


def validate_response_totals(*, draft_text: str, trace_steps: list[dict]) -> tuple[bool, str]:
    ctx = _parse_tool_payloads(trace_steps)
    expected_total = ctx.get("order_total")

    if expected_total is None:
        delivery = ctx.get("delivery_xof")
        if delivery is not None and ctx.get("article_prices"):
            # Pas de commande créée : on ne force pas de total dans le texte
            return True, "Aucune commande finalisée, contrôle total ignoré."

        return True, "Pas de total de commande à vérifier."

    numbers = [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", draft_text)]
    for num in numbers:
        if abs(num - expected_total) < 1.0:
            return True, f"Total {expected_total} XOF retrouvé dans la réponse."

    if str(int(expected_total)) in draft_text.replace(" ", ""):
        return True, f"Total {expected_total} XOF retrouvé (format entier)."

    return (
        False,
        f"Total attendu {expected_total} XOF non trouvé clairement dans la réponse.",
    )
