import asyncio
import json

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

from agent.data_store import load_orders, save_orders, load_stock, save_stock
from agent.multi.orchestrator import run_team_agent
from agent.runner import stream_agent_reply
from config import DEFAULT_MODEL, get_rodiumai_api_key

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "boutique-intelligente"})


@app.post("/chat")
def chat():
    try:
        get_rodiumai_api_key()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message requis"}), 400

    mode = body.get("mode") or "single"
    model = body.get("model") or DEFAULT_MODEL
    history = body.get("history") or []

    if mode == "team":

        async def team_generate():
            result = await run_team_agent(user_message=message, model=model, evaluate=True)
            reply = result["reply"]
            chunk_size = 48
            for i in range(0, len(reply), chunk_size):
                yield f"data: {json.dumps({'type': 'delta', 'content': reply[i:i+chunk_size]}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'trace', 'steps': result['trace']}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'agent_complete', 'usage': result.get('usage'), 'elapsed_ms': result.get('elapsed_ms'), 'mode': 'team'}, ensure_ascii=False)}\n\n"

        def team_bridge():
            loop = asyncio.new_event_loop()
            try:
                agen = team_generate()
                while True:
                    try:
                        chunk = loop.run_until_complete(agen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()

        return Response(
            stream_with_context(team_bridge()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def generate():
        async for chunk in stream_agent_reply(
            user_message=message,
            history=history,
            model=model,
            evaluate=True,
        ):
            yield chunk

    def sync_bridge():
        loop = asyncio.new_event_loop()
        try:
            agen = generate()
            while True:
                try:
                    chunk = loop.run_until_complete(agen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    return Response(
        stream_with_context(sync_bridge()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/orders")
def list_orders():
    status = request.args.get("status")
    orders = load_orders()
    if status:
        orders = [o for o in orders if o.get("statut") == status]
    return jsonify({"orders": orders})


def _apply_stock_for_order(order: dict, *, decrement: bool) -> None:
    stock_rows = {row["product_id"]: row for row in load_stock()}
    sign = -1 if decrement else 1
    for line in order.get("lignes") or []:
        pid = line.get("product_id")
        qty = int(line.get("quantite", 0))
        if pid not in stock_rows:
            stock_rows[pid] = {"product_id": pid, "quantite": 0, "seuil_alerte": 2}
        stock_rows[pid]["quantite"] = max(0, int(stock_rows[pid].get("quantite", 0)) + sign * qty)
    save_stock(list(stock_rows.values()))


@app.post("/orders/<order_id>/approve")
def approve_order(order_id: str):
    body = request.get_json(silent=True) or {}
    approved = body.get("approved", True)
    orders = load_orders()
    updated = None
    for order in orders:
        if order.get("id") != order_id:
            continue
        if order.get("statut") != "pending_manager":
            return jsonify({"error": "Commande non en attente gérante.", "statut": order.get("statut")}), 400
        order["statut"] = "confirmed" if approved else "rejected"
        updated = order
        if approved:
            _apply_stock_for_order(order, decrement=True)
        break

    if not updated:
        return jsonify({"error": "Commande introuvable."}), 404

    save_orders(orders)
    return jsonify({"order": updated})


if __name__ == "__main__":
    import os

    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1", threaded=True)
