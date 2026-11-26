// Waiting orders (cancel / change) and trade history (with CSV download).

import { useEffect, useState } from "react";
import { api } from "../api";
import { dateTimeText, money, pnlClass } from "../format";

export default function Orders() {
  const [tab, setTab] = useState("PENDING");
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");

  const load = () => api("/orders").then(setOrders);
  useEffect(() => {
    load();
  }, []);

  const shown = orders.filter((o) => (tab === "PENDING" ? o.status === "PENDING" : o.status !== "PENDING"));

  async function cancel(id) {
    try {
      await api(`/orders/${id}`, { method: "DELETE" });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function change(order) {
    const answer = window.prompt("New price for this order:", order.limit_price);
    if (!answer) return;
    try {
      await api(`/orders/${order.id}`, { method: "PATCH", body: { limit_price: Number(answer) } });
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function download() {
    const response = await api("/trades/export", { raw: true });
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = "trades.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page stack">
      <div className="spread">
        <div>
          <h1>Orders</h1>
          <div className="muted">Waiting orders fill when the live price reaches your price.</div>
        </div>
        <button onClick={download}>Download trades (CSV)</button>
      </div>

      <div className="tabs">
        <button className={tab === "PENDING" ? "on" : ""} onClick={() => setTab("PENDING")}>Waiting</button>
        <button className={tab === "HISTORY" ? "on" : ""} onClick={() => setTab("HISTORY")}>History</button>
      </div>
      {error && <div className="message error">{error}</div>}

      <div className="card">
        {shown.length === 0 && <div className="muted">Nothing here yet.</div>}
        {shown.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Order</th><th className="num">Qty</th><th className="num">Price</th>
                <th className="num">Charges</th><th className="num">Profit</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {shown.map((o) => (
                <tr key={o.id}>
                  <td>{dateTimeText(o.filled_at || o.created_at)}</td>
                  <td>
                    <span className={o.side === "BUY" ? "green" : "red"}>{o.side}</span> {o.symbol}
                    <div className="muted">{o.order_type.replace("_", " ")} {o.source === "AI" && "· from AI idea"}</div>
                  </td>
                  <td className="num">{o.quantity}</td>
                  <td className="num">{money(o.fill_price || o.limit_price)}</td>
                  <td className="num">{o.status === "FILLED" ? money(o.charges) : "-"}</td>
                  <td className={`num ${pnlClass(o.realized_pnl)}`}>{o.side === "SELL" && o.status === "FILLED" ? money(o.realized_pnl) : "-"}</td>
                  <td>
                    <span className="badge">{o.status}</span>
                    {o.reject_reason && <div className="muted">{o.reject_reason}</div>}
                  </td>
                  <td className="num">
                    {o.status === "PENDING" && (
                      <div className="row">
                        <button className="small" onClick={() => change(o)}>Change</button>
                        <button className="small" onClick={() => cancel(o.id)}>Cancel</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
