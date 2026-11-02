import json
import time

import httpx

_rate_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SEC = 3600


async def convertir_devise(*, montant_xof: float, devise_cible: str = "EUR") -> str:
    target = devise_cible.upper().strip()
    if target == "XOF":
        return json.dumps(
            {
                "montant_xof": montant_xof,
                "devise_cible": "XOF",
                "montant_converti": montant_xof,
                "taux": 1.0,
            },
            ensure_ascii=False,
        )

    xof_per_eur = 655.957

    if target == "EUR":
        rate = 1.0 / xof_per_eur
        return json.dumps(
            {
                "montant_xof": montant_xof,
                "devise_cible": "EUR",
                "montant_converti": round(montant_xof * rate, 2),
                "taux": round(rate, 8),
                "source": "parité XOF/EUR (655.957)",
            },
            ensure_ascii=False,
        )

    cache_key = target
    now = time.time()
    if cache_key in _rate_cache:
        ts, cached = _rate_cache[cache_key]
        if now - ts < CACHE_TTL_SEC:
            rate = cached["rate"]
            return json.dumps(
                {
                    "montant_xof": montant_xof,
                    "devise_cible": target,
                    "montant_converti": round(montant_xof * rate, 2),
                    "taux": rate,
                    "source": "frankfurter (cache)",
                    "date": cached.get("date"),
                },
                ensure_ascii=False,
            )

    url = f"https://api.frankfurter.dev/v1/latest?from=EUR&to={target}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        return json.dumps(
            {
                "error": f"API de change indisponible: {exc}",
                "montant_xof": montant_xof,
                "devise_cible": target,
            },
            ensure_ascii=False,
        )

    eur_to_target = float(data["rates"].get(target, 0))
    if eur_to_target <= 0:
        return json.dumps(
            {"error": f"Devise {target} non supportée.", "montant_xof": montant_xof},
            ensure_ascii=False,
        )

    rate = eur_to_target / xof_per_eur
    _rate_cache[cache_key] = (now, {"rate": rate, "date": data.get("date")})

    return json.dumps(
        {
            "montant_xof": montant_xof,
            "devise_cible": target,
            "montant_converti": round(montant_xof * rate, 2),
            "taux": round(rate, 8),
            "source": "frankfurter.app",
            "date": data.get("date"),
        },
        ensure_ascii=False,
    )
