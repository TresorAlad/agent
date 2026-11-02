import { useCallback, useEffect, useState } from "react";
import { approveOrder, fetchPendingOrders, type Order } from "../api";

export function OrderApproval() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchPendingOrders();
      setOrders(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
    const id = window.setInterval(reload, 8000);
    return () => window.clearInterval(id);
  }, [reload]);

  async function handleDecision(orderId: string, approved: boolean) {
    try {
      await approveOrder(orderId, approved);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur");
    }
  }

  return (
    <section className="orders-panel">
      <h2>Validation gérante</h2>
      <p className="subtitle">Commandes en attente (pending_manager)</p>
      {loading && <p>Chargement...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && orders.length === 0 && (
        <p className="hint">Aucune commande en attente.</p>
      )}
      <ul className="orders-list">
        {orders.map((order) => (
          <li key={order.id} className="order-card">
            <div className="order-head">
              <strong>{order.id}</strong>
              <span>{order.client_phone}</span>
            </div>
            <ul>
              {order.lignes.map((l, i) => (
                <li key={i}>
                  {l.quantite} x {l.nom} - {l.sous_total_xof} XOF
                </li>
              ))}
            </ul>
            <p>
              Livraison : {order.livraison_xof} XOF | Total : {order.total_xof} XOF
            </p>
            <div className="order-actions">
              <button type="button" onClick={() => handleDecision(order.id, true)}>
                Approuver
              </button>
              <button
                type="button"
                className="danger"
                onClick={() => handleDecision(order.id, false)}
              >
                Refuser
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
