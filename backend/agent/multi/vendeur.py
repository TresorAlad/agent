import json

from agent.llm import chat_completion, extract_assistant_message, parse_tool_arguments
from agent.tools.execute import execute_tool
from agent.tools.schemas import VENDEUR_TOOLS
from config import DEFAULT_MODEL, MAX_TOOL_ROUNDS

VENDEUR_SYSTEM = """Tu es le Vendeur de la boutique Dantokpa.
Tu gères catalogue, stock et conversion de devise. Utilise les outils.
Réponds en JSON compact : {"notes": "...", "tool_results": [...]} après tes appels outils."""


async def run_vendeur(*, user_message: str, context: dict, model: str = DEFAULT_MODEL) -> dict:
    messages = [
        {"role": "system", "content": VENDEUR_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                {"message_client": user_message, "contexte_gerant": context},
                ensure_ascii=False,
            ),
        },
    ]
    tool_results: list[dict] = []

    for _ in range(MAX_TOOL_ROUNDS):
        data = await chat_completion(model=model, messages=messages, tools=VENDEUR_TOOLS)
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

    return {"role": "vendeur", "tool_results": tool_results, "messages": messages}
