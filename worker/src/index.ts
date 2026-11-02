import { runAgent } from "./agent/runner";
import { isDuplicate } from "./dedup";
import type { Env } from "./env";
import { sendWhatsAppMessage } from "./green-api";
import { parseManagerDecision, sanitizeUserInput } from "./sanitize";
import { appendSessionTurn, loadSession } from "./session";
import { loadOrders, updateOrderStatus } from "./storage";

type GreenWebhookBody = {
  typeWebhook?: string;
  idMessage?: string;
  senderData?: { chatId?: string; sender?: string };
  messageData?: { textMessageData?: { textMessage?: string } };
};

async function notifyManager(env: Env, orderId: string): Promise<void> {
  const orders = await loadOrders(env.BOUTIQUE_KV);
  const order = orders.find((o) => o.id === orderId);
  if (!order || order.statut !== "pending_manager") return;

  const managerChat = `${env.MANAGER_PHONE.replace(/\D/g, "")}@c.us`;
  const recap = [
    "Nouvelle commande à valider:",
    order.id,
    `Client: ${order.client_phone}`,
    `Total: ${order.total_xof} XOF`,
    `Répondre: OUI ${order.id} ou NON ${order.id}`,
  ].join("\n");
  await sendWhatsAppMessage(env, managerChat, recap);
}

async function processMessage(env: Env, body: GreenWebhookBody): Promise<void> {
  const messageId = body.idMessage ?? crypto.randomUUID();
  if (await isDuplicate(env.BOUTIQUE_KV, messageId)) return;

  const chatId = body.senderData?.chatId;
  const sender = body.senderData?.sender ?? "";
  const text = body.messageData?.textMessageData?.textMessage?.trim() ?? "";
  if (!chatId || !text) return;

  const managerDecision = parseManagerDecision(text, env.MANAGER_PHONE, sender);
  if (managerDecision.isManager && managerDecision.orderId) {
    const statut = managerDecision.approved ? "confirmed" : "rejected";
    const updated = await updateOrderStatus(env.BOUTIQUE_KV, managerDecision.orderId, statut);
    const reply = updated
      ? `Commande ${updated.id} ${statut === "confirmed" ? "approuvée" : "refusée"}.`
      : "Commande introuvable.";
    await sendWhatsAppMessage(env, chatId, reply);
    if (updated && statut === "confirmed") {
      const clientChat = `${updated.client_phone.replace(/\D/g, "")}@c.us`;
      await sendWhatsAppMessage(
        env,
        clientChat,
        `Bonne nouvelle ! Votre commande ${updated.id} est confirmée par la gérante.`,
      );
    }
    return;
  }

  const check = sanitizeUserInput(text);
  if (!check.allowed) {
    await sendWhatsAppMessage(env, chatId, "Je ne peux pas traiter cette demande. Parlons de nos pagnes 😊");
    return;
  }

  const history = await loadSession(env.BOUTIQUE_KV, chatId);
  const reply = await runAgent(env, text, sender.replace("@c.us", ""), history);
  await sendWhatsAppMessage(env, chatId, reply);
  await appendSessionTurn(env.BOUTIQUE_KV, chatId, text, reply);

  const orders = await loadOrders(env.BOUTIQUE_KV);
  const pending = orders.filter(
    (o) => o.statut === "pending_manager" && o.client_phone.includes(sender.replace("@c.us", "")),
  );
  if (pending.length) {
    await notifyManager(env, pending[pending.length - 1].id);
  }
}

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    if (url.pathname === "/health") {
      return Response.json({ status: "ok", service: "boutique-worker" }, { headers: corsHeaders });
    }

    if (url.pathname === "/orders" && request.method === "GET") {
      const status = url.searchParams.get("status");
      let orders = await loadOrders(env.BOUTIQUE_KV);
      if (status) orders = orders.filter((o) => o.statut === status);
      return Response.json({ orders, source: "worker" }, { headers: corsHeaders });
    }

    const approveMatch = url.pathname.match(/^\/orders\/([^/]+)\/approve$/);
    if (approveMatch && request.method === "POST") {
      const orderId = approveMatch[1];
      let approved = true;
      try {
        const body = (await request.json()) as { approved?: boolean };
        approved = body.approved ?? true;
      } catch {
        /* empty body ok */
      }
      const statut = approved ? "confirmed" : "rejected";
      const updated = await updateOrderStatus(env.BOUTIQUE_KV, orderId, statut);
      if (!updated) {
        return Response.json({ error: "Commande introuvable." }, { status: 404, headers: corsHeaders });
      }
      const clientChat = `${String(updated.client_phone).replace(/\D/g, "")}@c.us`;
      const clientMsg =
        statut === "confirmed"
          ? `Bonne nouvelle ! Votre commande ${updated.id} est confirmée par la gérante. Merci !`
          : `Votre commande ${updated.id} n'a pas pu être validée. Contactez-nous au marché Dantokpa.`;
      try {
        await sendWhatsAppMessage(env, clientChat, clientMsg);
      } catch (err) {
        console.error("notify client after approve", err);
      }
      return Response.json({ order: updated, source: "worker" }, { headers: corsHeaders });
    }

    if (url.pathname === "/webhook" && request.method === "POST") {
      let body: GreenWebhookBody = {};
      try {
        body = (await request.json()) as GreenWebhookBody;
      } catch {
        return new Response("invalid json", { status: 400 });
      }

      if (body.typeWebhook && body.typeWebhook !== "incomingMessageReceived") {
        return new Response("ok");
      }

      ctx.waitUntil(
        processMessage(env, body).catch((err) => {
          console.error("processMessage", err);
        }),
      );
      return new Response("ok");
    }

    return new Response(
      "Boutique Dantokpa Worker - endpoints: /health, /webhook, /orders",
      { status: 404, headers: corsHeaders },
    );
  },
};
