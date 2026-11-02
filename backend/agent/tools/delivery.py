import json

# Tarifs fixes en XOF (FCFA)
DELIVERY_ZONES: dict[str, dict] = {
    "dantokpa": {
        "label": "Marché Dantokpa (retrait sur place)",
        "frais_xof": 0,
    },
    "cotonou_intra": {
        "label": "Cotonou intra-muros (Akpakpa, Cadjehoun, Ganhi...)",
        "frais_xof": 1500,
    },
    "agglomeration": {
        "label": "Agglomération Cotonou (Calavi, Godomey...)",
        "frais_xof": 2500,
    },
    "inter_villes": {
        "label": "Inter-villes (Porto-Novo, Ouidah, Parakou...)",
        "frais_xof": 4500,
    },
}

ZONE_ALIASES: dict[str, str] = {
    "dantokpa": "dantokpa",
    "marche": "dantokpa",
    "akpakpa": "cotonou_intra",
    "cadjehoun": "cotonou_intra",
    "ganhi": "cotonou_intra",
    "cotonou": "cotonou_intra",
    "calavi": "agglomeration",
    "godomey": "agglomeration",
    "porto-novo": "inter_villes",
    "porto novo": "inter_villes",
    "ouidah": "inter_villes",
    "parakou": "inter_villes",
}


def _resolve_zone(zone: str) -> str | None:
    key = zone.lower().strip()
    if key in DELIVERY_ZONES:
        return key
    for alias, resolved in ZONE_ALIASES.items():
        if alias in key or key in alias:
            return resolved
    return None


def calculer_livraison(*, zone: str, poids_kg: float = 1.0) -> str:
    resolved = _resolve_zone(zone)
    if not resolved:
        return json.dumps(
            {
                "error": "Zone non reconnue.",
                "zone_saisie": zone,
                "zones_connues": list(DELIVERY_ZONES.keys()),
            },
            ensure_ascii=False,
        )

    info = DELIVERY_ZONES[resolved]
    extra = 0
    if poids_kg > 2:
        extra = int((poids_kg - 2) * 500)

    frais = info["frais_xof"] + extra

    return json.dumps(
        {
            "zone": resolved,
            "zone_label": info["label"],
            "poids_kg": poids_kg,
            "frais_livraison_xof": frais,
            "delai_estime": "24-48h" if resolved != "dantokpa" else "retrait immédiat",
        },
        ensure_ascii=False,
    )
