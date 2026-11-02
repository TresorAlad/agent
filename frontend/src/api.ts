export type AgentMode = "single" | "team";

export type TraceStep = {
  step: number;
  kind: string;
  tool?: string | null;
  args_summary?: string | null;
  result_summary?: string | null;
  ts?: string;
  meta?: Record<string, unknown>;
};

export type Order = {
  id: string;
  client_phone: string;
  statut: string;
  total_xof: number;
  livraison_xof: number;
  lignes: Array<{ nom: string; quantite: number; sous_total_xof: number }>;
  created_at?: string;
};

export async function streamChat(
  message: string,
  mode: AgentMode,
  onEvent: (payload: Record<string, unknown>) => void,
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err || "Erreur chat");
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Flux SSE indisponible");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data: ")) continue;
      try {
        onEvent(JSON.parse(line.slice(6)) as Record<string, unknown>);
      } catch {
        /* ignore malformed chunk */
      }
    }
  }
}

export async function fetchPendingOrders(): Promise<Order[]> {
  const res = await fetch("/api/orders?status=pending_manager");
  if (!res.ok) throw new Error("Impossible de charger les commandes");
  const data = (await res.json()) as { orders: Order[] };
  return data.orders;
}

export async function approveOrder(orderId: string, approved: boolean): Promise<Order> {
  const res = await fetch(`/api/orders/${orderId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }
  const data = (await res.json()) as { order: Order };
  return data.order;
}
