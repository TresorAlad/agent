import json

from agent.llm import chat_completion, extract_assistant_message
from config import DEFAULT_MODEL


JUDGE_SYSTEM = """Tu es un juge qualité pour un vendeur WhatsApp boutique.
Évalue si la réponse respecte :
- pas de prix/stock inventés (doit s'appuyer sur les faits fournis)
- ton WhatsApp adapté (court, clair)
- rupture gérée si mentionnée dans le contexte
- pas de confirmation de commande sans validation gérante si une commande est pending_manager

Réponds UNIQUEMENT en JSON : {"approved": true/false, "score": 0-10, "feedback": "..."}"""


async def judge_response(
    *,
    user_message: str,
    draft_reply: str,
    tool_context: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Message client:\n{user_message}\n\n"
                f"Contexte outils:\n{tool_context}\n\n"
                f"Brouillon réponse:\n{draft_reply}"
            ),
        },
    ]
    data = await chat_completion(model=model, messages=messages, max_tokens=512)
    assistant = extract_assistant_message(data)
    raw = (assistant.get("content") or "").strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    approved = "approved" in raw.lower() and "true" in raw.lower()
    return {
        "approved": approved,
        "score": 7 if approved else 4,
        "feedback": raw[:300],
    }
