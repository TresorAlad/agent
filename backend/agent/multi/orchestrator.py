import json
import time

from agent.evaluation.judge import judge_response
from agent.evaluation.totals import validate_response_totals
from agent.multi.logisticien import run_logisticien
from agent.multi.redacteur import run_redacteur
from agent.multi.vendeur import run_vendeur
from agent.trace import TraceCollector, summarize_result
from config import DEFAULT_MODEL


GERANT_SYSTEM = """Tu es le Gérant. Analyse la demande client et produis un plan JSON :
{"besoin_vendeur": true/false, "besoin_logisticien": true/false, "notes": "..."}
Ne réponds qu'avec ce JSON."""


async def _plan_gerant(*, user_message: str, model: str) -> dict:
    from agent.llm import chat_completion, extract_assistant_message

    data = await chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": GERANT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        max_tokens=256,
    )
    assistant = extract_assistant_message(data)
    raw = (assistant.get("content") or "").strip()
    try:
        plan = json.loads(raw)
        if isinstance(plan, dict):
            return plan
    except json.JSONDecodeError:
        pass
    lower = user_message.lower()
    return {
        "besoin_vendeur": any(w in lower for w in ("pagne", "wax", "stock", "euro", "prix", "produit")),
        "besoin_logisticien": any(w in lower for w in ("livraison", "akpakpa", "dantokpa", "calavi", "livrer")),
        "notes": raw[:200],
    }


async def run_team_agent(
    *,
    user_message: str,
    model: str = DEFAULT_MODEL,
    evaluate: bool = True,
) -> dict:
    started = time.perf_counter()
    trace = TraceCollector()
    trace.add(kind="start", tool=None, meta={"mode": "team"})

    plan = await _plan_gerant(user_message=user_message, model=model)
    trace.add(kind="plan", tool="gerant", result_summary=json.dumps(plan, ensure_ascii=False))

    consolidated: dict = {"plan": plan, "vendeur": None, "logisticien": None}
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    if plan.get("besoin_vendeur", True):
        vendeur_out = await run_vendeur(user_message=user_message, context=plan, model=model)
        consolidated["vendeur"] = vendeur_out
        for tr in vendeur_out.get("tool_results") or []:
            trace.add(
                kind="tool_result",
                tool=tr.get("tool"),
                args_summary=json.dumps(tr.get("args"), ensure_ascii=False)[:120],
                result_summary=summarize_result(tr.get("result") or ""),
            )

    if plan.get("besoin_logisticien", True):
        log_out = await run_logisticien(user_message=user_message, context=consolidated, model=model)
        consolidated["logisticien"] = log_out
        for tr in log_out.get("tool_results") or []:
            trace.add(
                kind="tool_result",
                tool=tr.get("tool"),
                args_summary=json.dumps(tr.get("args"), ensure_ascii=False)[:120],
                result_summary=summarize_result(tr.get("result") or ""),
            )

    draft = await run_redacteur(user_message=user_message, consolidated=consolidated, model=model)
    trace.add(kind="draft", tool="redacteur", result_summary=summarize_result(draft))

    final_text = draft
    judge_result = None
    totals_ok = True
    totals_msg = ""

    if evaluate:
        totals_ok, totals_msg = validate_response_totals(
            draft_text=draft, trace_steps=trace.to_list()
        )
        trace.add(kind="evaluation", tool="totals", result_summary=totals_msg, meta={"ok": totals_ok})

        tool_context = json.dumps(trace.to_list(), ensure_ascii=False)[:4000]
        judge_result = await judge_response(
            user_message=user_message,
            draft_reply=draft,
            tool_context=tool_context,
            model=model,
        )
        trace.add(
            kind="evaluation",
            tool="judge",
            result_summary=json.dumps(judge_result, ensure_ascii=False),
        )
        if (not totals_ok or not judge_result.get("approved")) and evaluate:
            feedback = judge_result.get("feedback") if judge_result else totals_msg
            final_text = await run_redacteur(
                user_message=user_message + f"\n[Correction requise: {feedback}]",
                consolidated=consolidated,
                model=model,
            )
            trace.add(kind="retry", tool="redacteur", result_summary=summarize_result(final_text))

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    trace.add(kind="complete", tool=None, meta={"elapsed_ms": elapsed_ms, "usage": usage_total})

    return {
        "reply": final_text,
        "trace": trace.to_list(),
        "judge": judge_result,
        "totals_ok": totals_ok,
        "elapsed_ms": elapsed_ms,
        "usage": usage_total,
    }
