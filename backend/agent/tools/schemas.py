TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "chercher_produit",
            "description": "Recherche un produit dans le catalogue (pagnes, accessoires).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Mot-clé ou description"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verifier_stock",
            "description": "Vérifie le stock d'un produit et propose des alternatives en rupture.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "quantite": {"type": "integer", "minimum": 1},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculer_livraison",
            "description": "Calcule les frais de livraison selon la zone (Dantokpa, Akpakpa, Calavi, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {"type": "string"},
                    "poids_kg": {"type": "number", "minimum": 0.1},
                },
                "required": ["zone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convertir_devise",
            "description": "Convertit un montant XOF vers une devise (EUR, USD, etc.) via API Frankfurter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "montant_xof": {"type": "number"},
                    "devise_cible": {"type": "string"},
                },
                "required": ["montant_xof", "devise_cible"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creer_commande",
            "description": (
                "Crée une commande. client_confirmed=true seulement après accord explicite du client. "
                "Ne confirme pas la vente : la gérante doit valider."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "client_phone": {"type": "string"},
                    "lignes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "quantite": {"type": "integer"},
                            },
                            "required": ["product_id", "quantite"],
                        },
                    },
                    "frais_livraison_xof": {"type": "number"},
                    "client_confirmed": {"type": "boolean"},
                    "devise_affichee": {"type": "string"},
                },
                "required": ["client_phone", "lignes", "frais_livraison_xof"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtenir_statut_commande",
            "description": "Lit le statut d'une commande existante.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
]

VENDEUR_TOOLS = [
    t for t in TOOL_DEFINITIONS if t["function"]["name"] in (
        "chercher_produit",
        "verifier_stock",
        "convertir_devise",
        "obtenir_statut_commande",
    )
]

LOGISTICIEN_TOOLS = [
    t for t in TOOL_DEFINITIONS if t["function"]["name"] == "calculer_livraison"
]

ORDER_TOOLS = [
    t for t in TOOL_DEFINITIONS if t["function"]["name"] in ("creer_commande", "obtenir_statut_commande")
]
