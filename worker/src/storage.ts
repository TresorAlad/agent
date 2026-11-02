import type { Env } from "./env";

const KEYS = {
  catalog: "data:catalog",
  stock: "data:stock",
  orders: "data:orders",
} as const;

export type CatalogItem = {
  id: string;
  nom: string;
  description: string;
  prix_xof: number;
  categorie: string;
  mots_cles: string[];
};

export type StockRow = { product_id: string; quantite: number; seuil_alerte: number };

export type Order = {
  id: string;
  client_phone: string;
  lignes: Array<Record<string, unknown>>;
  livraison_xof: number;
  total_xof: number;
  devise_affichee: string;
  statut: string;
  created_at: string;
};

async function readJson<T>(kv: KVNamespace, key: string, fallback: T): Promise<T> {
  const raw = await kv.get(key);
  if (!raw) return fallback;
  return JSON.parse(raw) as T;
}

async function writeJson(kv: KVNamespace, key: string, value: unknown): Promise<void> {
  await kv.put(key, JSON.stringify(value));
}

export async function ensureSeedData(kv: KVNamespace): Promise<void> {
  const catalog = await kv.get(KEYS.catalog);
  if (catalog) return;

  const seedCatalog: CatalogItem[] = [
    {
      id: "pagne-wax-bleu",
      nom: "Pagne wax bleu royal",
      description: "Wax 6 yards",
      prix_xof: 8500,
      categorie: "pagne",
      mots_cles: ["wax", "bleu"],
    },
    {
      id: "pagne-ankara",
      nom: "Pagne ankara fleurs",
      description: "Ankara coloré",
      prix_xof: 7800,
      categorie: "pagne",
      mots_cles: ["ankara"],
    },
  ];
  const seedStock: StockRow[] = [
    { product_id: "pagne-wax-bleu", quantite: 12, seuil_alerte: 3 },
    { product_id: "pagne-ankara", quantite: 18, seuil_alerte: 4 },
  ];
  await writeJson(kv, KEYS.catalog, seedCatalog);
  await writeJson(kv, KEYS.stock, seedStock);
  await writeJson(kv, KEYS.orders, []);
}

export async function loadCatalog(kv: KVNamespace): Promise<CatalogItem[]> {
  await ensureSeedData(kv);
  return readJson(kv, KEYS.catalog, []);
}

export async function loadStock(kv: KVNamespace): Promise<StockRow[]> {
  await ensureSeedData(kv);
  return readJson(kv, KEYS.stock, []);
}

export async function saveStock(kv: KVNamespace, stock: StockRow[]): Promise<void> {
  await writeJson(kv, KEYS.stock, stock);
}

export async function loadOrders(kv: KVNamespace): Promise<Order[]> {
  await ensureSeedData(kv);
  return readJson(kv, KEYS.orders, []);
}

export async function saveOrders(kv: KVNamespace, orders: Order[]): Promise<void> {
  await writeJson(kv, KEYS.orders, orders);
}

export async function updateOrderStatus(
  kv: KVNamespace,
  orderId: string,
  statut: string,
): Promise<Order | null> {
  const orders = await loadOrders(kv);
  let updated: Order | null = null;
  for (const order of orders) {
    if (order.id !== orderId) continue;
    order.statut = statut;
    updated = order;
    if (statut === "confirmed") {
      const stock = await loadStock(kv);
      const map = new Map(stock.map((s) => [s.product_id, s]));
      for (const line of order.lignes) {
        const pid = String(line.product_id);
        const qty = Number(line.quantite ?? 1);
        const row = map.get(pid) ?? { product_id: pid, quantite: 0, seuil_alerte: 2 };
        row.quantite = Math.max(0, row.quantite - qty);
        map.set(pid, row);
      }
      await saveStock(kv, [...map.values()]);
    }
  }
  if (!updated) return null;
  await saveOrders(kv, orders);
  return updated;
}
