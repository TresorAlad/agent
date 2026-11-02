import {
  loadCatalog,
  loadOrders,
  loadStock,
  saveOrders,
  type CatalogItem,
} from "../storage";
import type { Env } from "../env";

const DELIVERY: Record<string, { label: string; frais_xof: number }> = {
  dantokpa: { label: "Dantokpa", frais_xof: 0 },
  cotonou_intra: { label: "Cotonou intra-muros", frais_xof: 1500 },
  agglomeration: { label: "Agglomération", frais_xof: 2500 },
  inter_villes: { label: "Inter-villes", frais_xof: 4500 },
};

function resolveZone(zone: string): string | null {
  const key = zone.toLowerCase();
  if (DELIVERY[key]) return key;
  if (key.includes("akpakpa") || key.includes("cotonou")) return "cotonou_intra";
  if (key.includes("dantokpa")) return "dantokpa";
  if (key.includes("calavi")) return "agglomeration";
  return null;
}

export async function executeTool(
  env: Env,
  name: string,
  args: Record<string, unknown>,
): Promise<string> {
  const kv = env.BOUTIQUE_KV;

  if (name === "chercher_produit") {
    const query = String(args.query ?? "").toLowerCase();
    const catalog = await loadCatalog(kv);
    const results = catalog.filter((p) =>
      [p.nom, p.description, p.mots_cles.join(" ")].join(" ").toLowerCase().includes(query),
    );
    return JSON.stringify({ query, produits: results.slice(0, 5) });
  }

  if (name === "verifier_stock") {
    const productId = String(args.product_id ?? "");
    const qty = Number(args.quantite ?? 1);
    const catalog = await loadCatalog(kv);
    const stock = await loadStock(kv);
    const product = catalog.find((p) => p.id === productId);
    if (!product) return JSON.stringify({ error: "Produit inconnu" });
    const row = stock.find((s) => s.product_id === productId);
    const availableQty = row?.quantite ?? 0;
    const available = availableQty >= qty;
    let alternatives: CatalogItem[] = [];
    if (!available) {
      alternatives = catalog.filter((p) => {
        if (p.id === productId || p.categorie !== product.categorie) return false;
        const s = stock.find((x) => x.product_id === p.id);
        return (s?.quantite ?? 0) > 0;
      });
    }
    return JSON.stringify({
      product_id: productId,
      stock_disponible: availableQty,
      available,
      alternatives: alternatives.slice(0, 3),
    });
  }

  if (name === "calculer_livraison") {
    const zone = resolveZone(String(args.zone ?? ""));
    if (!zone) return JSON.stringify({ error: "Zone non reconnue" });
    const info = DELIVERY[zone];
    return JSON.stringify({ zone, zone_label: info.label, frais_livraison_xof: info.frais_xof });
  }

  if (name === "convertir_devise") {
    const montant = Number(args.montant_xof ?? 0);
    const target = String(args.devise_cible ?? "EUR").toUpperCase();
    const xofPerEur = 655.957;
    if (target === "EUR") {
      const rate = 1 / xofPerEur;
      return JSON.stringify({
        montant_xof: montant,
        devise_cible: target,
        montant_converti: Math.round(montant * rate * 100) / 100,
        taux: rate,
      });
    }
    const res = await fetch(`https://api.frankfurter.dev/v1/latest?from=EUR&to=${target}`);
    if (!res.ok) return JSON.stringify({ error: "API change indisponible", montant_xof: montant });
    const data = (await res.json()) as { rates: Record<string, number> };
    const eurToTarget = data.rates[target] ?? 0;
    const rate = eurToTarget / xofPerEur;
    return JSON.stringify({
      montant_xof: montant,
      devise_cible: target,
      montant_converti: Math.round(montant * rate * 100) / 100,
      taux: rate,
    });
  }

  if (name === "creer_commande") {
    const catalog = await loadCatalog(kv);
    const map = new Map(catalog.map((p) => [p.id, p]));
    const lines = (args.lignes as Array<{ product_id: string; quantite: number }>) ?? [];
    let totalArticles = 0;
    const normalized = [];
    for (const line of lines) {
      const p = map.get(line.product_id);
      if (!p) return JSON.stringify({ error: `Produit inconnu ${line.product_id}` });
      const sub = p.prix_xof * line.quantite;
      totalArticles += sub;
      normalized.push({
        product_id: p.id,
        nom: p.nom,
        quantite: line.quantite,
        sous_total_xof: sub,
      });
    }
    const livraison = Number(args.frais_livraison_xof ?? 0);
    const total = totalArticles + livraison;
    const clientConfirmed = Boolean(args.client_confirmed);
    const orderId = `CMD-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
    const order = {
      id: orderId,
      client_phone: String(args.client_phone ?? "unknown"),
      lignes: normalized,
      livraison_xof: livraison,
      total_xof: total,
      devise_affichee: String(args.devise_affichee ?? "XOF"),
      statut: clientConfirmed ? "pending_manager" : "pending_client",
      created_at: new Date().toISOString(),
    };
    const orders = await loadOrders(kv);
    orders.push(order);
    await saveOrders(kv, orders);
    return JSON.stringify({ id: orderId, statut: order.statut, total_xof: total });
  }

  return JSON.stringify({ error: `Outil inconnu ${name}` });
}

export const TOOL_DEFINITIONS = [
  {
    type: "function",
    function: {
      name: "chercher_produit",
      parameters: {
        type: "object",
        properties: { query: { type: "string" } },
        required: ["query"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "verifier_stock",
      parameters: {
        type: "object",
        properties: {
          product_id: { type: "string" },
          quantite: { type: "integer" },
        },
        required: ["product_id"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "calculer_livraison",
      parameters: {
        type: "object",
        properties: { zone: { type: "string" } },
        required: ["zone"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "convertir_devise",
      parameters: {
        type: "object",
        properties: {
          montant_xof: { type: "number" },
          devise_cible: { type: "string" },
        },
        required: ["montant_xof", "devise_cible"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "creer_commande",
      parameters: {
        type: "object",
        properties: {
          client_phone: { type: "string" },
          lignes: { type: "array" },
          frais_livraison_xof: { type: "number" },
          client_confirmed: { type: "boolean" },
        },
        required: ["client_phone", "lignes", "frais_livraison_xof"],
      },
    },
  },
];
