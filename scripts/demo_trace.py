#!/usr/bin/env python3
"""Scénario palier 1 : une demande déclenche plusieurs outils enchaînés."""

import asyncio
import json
import os
import sys

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND)

from agent.runner import stream_agent_reply  # noqa: E402


async def main() -> None:
    message = (
        "Bonjour, je veux 2 pagnes wax bleu livrés à Akpakpa. "
        "Donne-moi aussi le total approximatif en euros s'il te plaît."
    )
    print("Message client:", message)
    print("-" * 60)

    trace_steps = []
    reply_parts = []

    async for chunk in stream_agent_reply(user_message=message, evaluate=False):
        if not chunk.startswith("data: "):
            continue
        payload = json.loads(chunk[6:].strip())
        t = payload.get("type")
        if t == "tool":
            print(f"[outil] {payload.get('name')} -> {payload.get('status')}")
        if t == "trace":
            trace_steps = payload.get("steps") or []
        if t == "delta":
            reply_parts.append(payload.get("content", ""))

    print("-" * 60)
    print("Réponse agent:", "".join(reply_parts))
    print("-" * 60)
    print("Trace JSON:")
    print(json.dumps(trace_steps, ensure_ascii=False, indent=2))
    tool_calls = [s for s in trace_steps if s.get("kind") == "tool_call"]
    print(f"\nNombre d'appels outils: {len(tool_calls)}")


if __name__ == "__main__":
    asyncio.run(main())
