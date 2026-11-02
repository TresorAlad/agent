import json
import time
from collections.abc import AsyncIterator

from agent.evaluation.judge import judge_response
from agent.evaluation.totals import validate_response_totals
from agent.llm import chat_completion, extract_assistant_message, parse_tool_arguments
from agent.tools.execute import execute_tool
from agent.tools.schemas import TOOL_DEFINITIONS
from agent.trace import TraceCollector, summarize_result
from config import DEFAULT_MODEL, MAX_TOOL_ROUNDS, load_vendeur_prompt


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_agent_reply(
    *,
    user_message: str,
    history: list[dict] | None = None,
    model: str = DEFAULT_MODEL,
    evaluate: bool = True,
) -> AsyncIterator[str]:
    started = time.perf_counter()
    trace = TraceCollector()
    trace.add(kind="start", tool=None, meta={"mode": "single"})

    working: list[dict] = [{"role": "system", "content": load_vendeur_prompt()}]
    if history:
        working.extend(history)
    working.append({"role": "user", "content": user_message})

    usage: dict | None = None
    tool_context_parts: list[str] = []

    try:
        for _ in range(MAX_TOOL_ROUNDS):
            data = await chat_completion(model=model, messages=working, tools=TOOL_DEFINITIONS)
            if data.get("usage"):
                usage = data["usage"]

            assistant = extract_assistant_message(data)
            tool_calls = assistant.get("tool_calls") or []

            if not tool_calls:
                draft = (assistant.get("content") or "").strip()
                if not draft:
                    yield _sse({"type": "error", "detail": "Réponse vide du modèle."})
                    return

                final_text = draft
                if evaluate:
                    totals_ok, totals_msg = validate_response_totals(
                        draft_text=draft, trace_steps=trace.to_list()
                    )
                    yield _sse(
                        {
                            "type": "evaluation",
                            "check": "totals",
                            "ok": totals_ok,
                            "detail": totals_msg,
                        }
                    )
                    trace.add(
                        kind="evaluation",
                        tool="totals",
                        result_summary=totals_msg,
                        meta={"ok": totals_ok},
                    )

                    judge = await judge_response(
                        user_message=user_message,
                        draft_reply=draft,
                        tool_context="\n".join(tool_context_parts)[:4000],
                        model=model,
                    )
                    yield _sse({"type": "evaluation", "check": "judge", "result": judge})
                    trace.add(
                        kind="evaluation",
                        tool="judge",
                        result_summary=json.dumps(judge, ensure_ascii=False),
                    )

                    if not totals_ok or not judge.get("approved"):
                        working.append({"role": "assistant", "content": draft})
                        working.append(
                            {
                                "role": "user",
                                "content": (
                                    "Corrige ta réponse : respecte les chiffres des outils et le format WhatsApp. "
                                    f"Feedback juge : {judge.get('feedback', totals_msg)}"
                                ),
                            }
                        )
                        retry_data = await chat_completion(model=model, messages=working)
                        if retry_data.get("usage") and usage:
                            for k, v in retry_data["usage"].items():
                                usage[k] = usage.get(k, 0) + v
                        retry_msg = extract_assistant_message(retry_data)
                        final_text = (retry_msg.get("content") or draft).strip()
                        trace.add(
                            kind="retry",
                            tool=None,
                            result_summary=summarize_result(final_text),
                        )

                elapsed_ms = int((time.perf_counter() - started) * 1000)
                trace.add(kind="complete", tool=None, meta={"elapsed_ms": elapsed_ms})

                chunk_size = 48
                for index in range(0, len(final_text), chunk_size):
                    yield _sse({"type": "delta", "content": final_text[index : index + chunk_size]})

                yield _sse(
                    {
                        "type": "trace",
                        "steps": trace.to_list(),
                    }
                )
                yield _sse(
                    {
                        "type": "agent_complete",
                        "usage": usage,
                        "elapsed_ms": elapsed_ms,
                    }
                )
                return

            working.append(
                {
                    "role": "assistant",
                    "content": assistant.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for call in tool_calls:
                fn = call.get("function") or {}
                name = fn.get("name") or "unknown"
                args = parse_tool_arguments(fn.get("arguments"))

                yield _sse({"type": "tool", "name": name, "status": "running", "args": args})
                trace.add(
                    kind="tool_call",
                    tool=name,
                    args_summary=json.dumps(args, ensure_ascii=False)[:160],
                )

                result = await execute_tool(name=name, arguments=args)
                tool_context_parts.append(f"{name}: {result}")

                trace.add(
                    kind="tool_result",
                    tool=name,
                    result_summary=summarize_result(result),
                )
                yield _sse(
                    {
                        "type": "tool",
                        "name": name,
                        "status": "done",
                        "result_preview": summarize_result(result, 120),
                    }
                )
                yield _sse({"type": "trace_step", "step": trace.to_list()[-1]})

                working.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": result,
                    }
                )

        yield _sse({"type": "error", "detail": "Nombre maximal d'appels d'outils atteint."})
    except RuntimeError as exc:
        yield _sse({"type": "error", "detail": str(exc)})
