export async function isDuplicate(kv: KVNamespace, messageId: string): Promise<boolean> {
  const key = `msg:${messageId}`;
  const existing = await kv.get(key);
  if (existing) return true;
  await kv.put(key, "1", { expirationTtl: 86400 });
  return false;
}
