import { runAgent } from "./agent/runner";
import { isDuplicate } from "./dedup";
import type { Env } from "./env";
import { sendWhatsAppMessage } from "./green-api";
import { parseManagerDecision, sanitizeUserInput } from "./sanitize";
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

  const reply = await runAgent(env, text, sender.replace("@c.us", ""));
  await sendWhatsAppMessage(env, chatId, reply);

  const orders = await loadOrders(env.BOUTIQUE_KV);
  const pending = orders.filter(
    (o) => o.statut === "pending_manager" && o.client_phone.includes(sender.replace("@c.us", "")),
  );
  if (pending.length) {
    await notifyManager(env, pending[pending.length - 1].id);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return Response.json({ status: "ok", service: "boutique-worker" });
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

    return new Response("Boutique Dantokpa Worker - endpoints: /health, /webhook", { status: 404 });
  },
};
