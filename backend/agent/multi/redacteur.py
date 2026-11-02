import json

from agent.llm import chat_completion, extract_assistant_message
from config import DEFAULT_MODEL

REDACTEUR_SYSTEM = """Tu es le Rédacteur WhatsApp. Tu reformules pour le client final.
Règles : messages courts, puces, ton chaleureux, aucun chiffre inventé (utilise uniquement le JSON consolidé).
Ne confirme jamais une commande si statut pending_manager ou pending_client."""


async def run_redacteur(*, user_message: str, consolidated: dict, model: str = DEFAULT_MODEL) -> str:
    messages = [
        {"role": "system", "content": REDACTEUR_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                {"message_client": user_message, "donnees_equipe": consolidated},
                ensure_ascii=False,
            ),
        },
    ]
    data = await chat_completion(model=model, messages=messages, max_tokens=1024)
    assistant = extract_assistant_message(data)
    return (assistant.get("content") or "").strip()
