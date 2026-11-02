import json
from typing import Any

import httpx

from config import RODIUMAI_URL, get_rodiumai_api_key


async def chat_completion(
    *,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict] | None = None,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            RODIUMAI_URL,
            headers={"Authorization": f"Bearer {get_rodiumai_api_key()}"},
            json=payload,
        )
        if response.status_code != 200:
            detail = response.text[:500]
            raise RuntimeError(f"Appel LLM échoué ({response.status_code}) : {detail}")
        return response.json()


def extract_assistant_message(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Réponse LLM sans choices.")
    message = choices[0].get("message")
    if not message:
        raise RuntimeError("Réponse LLM sans message.")
    return message


def parse_tool_arguments(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
