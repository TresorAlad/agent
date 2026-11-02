import json

from agent.llm import chat_completion, extract_assistant_message, parse_tool_arguments
from agent.tools.execute import execute_tool
from agent.tools.schemas import LOGISTICIEN_TOOLS
from config import DEFAULT_MODEL, MAX_TOOL_ROUNDS

LOGISTICIEN_SYSTEM = """Tu es le Logisticien. Tu calcules uniquement la livraison via l'outil calculer_livraison.
Réponds avec les faits outils, sans inventer de tarif."""


async def run_logisticien(*, user_message: str, context: dict, model: str = DEFAULT_MODEL) -> dict:
    messages = [
        {"role": "system", "content": LOGISTICIEN_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                {"message_client": user_message, "contexte": context},
                ensure_ascii=False,
            ),
        },
    ]
    tool_results: list[dict] = []

    for _ in range(min(3, MAX_TOOL_ROUNDS)):
        data = await chat_completion(model=model, messages=messages, tools=LOGISTICIEN_TOOLS)
        assistant = extract_assistant_message(data)
        tool_calls = assistant.get("tool_calls") or []
        if not tool_calls:
            break

        messages.append(
            {
                "role": "assistant",
                "content": assistant.get("content"),
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            fn = call.get("function") or {}
            name = fn.get("name") or ""
            args = parse_tool_arguments(fn.get("arguments"))
            result = await execute_tool(name=name, arguments=args)
            tool_results.append({"tool": name, "args": args, "result": result})
            messages.append(
                {"role": "tool", "tool_call_id": call.get("id"), "content": result}
            )

    return {"role": "logisticien", "tool_results": tool_results}
