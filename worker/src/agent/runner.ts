import type { Env } from "../env";
import { executeTool, TOOL_DEFINITIONS } from "./tools";

const SYSTEM_PROMPT = `Tu es le vendeur WhatsApp de la boutique Tissus Dantokpa.
Ne jamais inventer prix, stock ou total. Utilise les outils.
Format WhatsApp court. Commande seulement avec accord client et validation gérante.`;

type ChatMessage = Record<string, unknown>;

async function chatCompletion(env: Env, messages: ChatMessage[]): Promise<any> {
  const response = await fetch("https://api.rodiumai.io/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.RODIUMAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: env.RODIUMAI_MODEL ?? "openai/gpt-4o-mini",
      messages,
      tools: TOOL_DEFINITIONS,
      tool_choice: "auto",
      max_tokens: 1024,
    }),
  });
  if (!response.ok) {
    throw new Error(`LLM error ${response.status}`);
  }
  return response.json();
}

export async function runAgent(env: Env, userMessage: string, clientPhone: string): Promise<string> {
  const messages: ChatMessage[] = [
    { role: "system", content: SYSTEM_PROMPT },
    {
      role: "user",
      content: `Client ${clientPhone} dit: ${userMessage}`,
    },
  ];

  for (let i = 0; i < 6; i++) {
    const data = await chatCompletion(env, messages);
    const assistant = data.choices?.[0]?.message;
    if (!assistant) return "Désolé, je ne peux pas répondre pour le moment.";

    const toolCalls = assistant.tool_calls ?? [];
    if (!toolCalls.length) {
      return String(assistant.content ?? "").trim() || "Merci pour votre message.";
    }

    messages.push({
      role: "assistant",
      content: assistant.content,
      tool_calls: toolCalls,
    });

    for (const call of toolCalls) {
      const fn = call.function ?? {};
      const name = String(fn.name ?? "");
      let args: Record<string, unknown> = {};
      try {
        args = JSON.parse(String(fn.arguments ?? "{}"));
      } catch {
        args = {};
      }
      if (name === "creer_commande" && !args.client_phone) {
        args.client_phone = clientPhone;
      }
      const result = await executeTool(env, name, args);
      messages.push({
        role: "tool",
        tool_call_id: call.id,
        content: result,
      });
    }
  }

  return "Je dois vérifier encore quelques informations. Pouvez-vous reformuler ?";
}
