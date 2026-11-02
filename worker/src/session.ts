export type SessionMessage = { role: "user" | "assistant"; content: string };

const MAX_MESSAGES = 16;
const TTL_SEC = 7 * 24 * 3600;

function sessionKey(chatId: string): string {
  return `session:${chatId}`;
}

export async function loadSession(kv: KVNamespace, chatId: string): Promise<SessionMessage[]> {
  const raw = await kv.get(sessionKey(chatId));
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as SessionMessage[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function saveSession(
  kv: KVNamespace,
  chatId: string,
  history: SessionMessage[],
): Promise<void> {
  const trimmed = history.slice(-MAX_MESSAGES);
  await kv.put(sessionKey(chatId), JSON.stringify(trimmed), { expirationTtl: TTL_SEC });
}

export async function appendSessionTurn(
  kv: KVNamespace,
  chatId: string,
  userText: string,
  assistantText: string,
): Promise<void> {
  const history = await loadSession(kv, chatId);
  history.push({ role: "user", content: userText });
  history.push({ role: "assistant", content: assistantText });
  await saveSession(kv, chatId, history);
}
