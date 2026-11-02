import type { Env } from "./env";

function baseUrl(env: Env): string {
  const host = (env.GREEN_API_URL ?? "https://api.green-api.com").replace(/\/$/, "");
  return `${host}/waInstance${env.GREEN_API_ID}`;
}

export async function sendWhatsAppMessage(
  env: Env,
  chatId: string,
  message: string,
): Promise<void> {
  const url = `${baseUrl(env)}/sendMessage/${env.GREEN_API_TOKEN}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chatId, message }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Green API sendMessage failed: ${detail.slice(0, 200)}`);
  }
}
