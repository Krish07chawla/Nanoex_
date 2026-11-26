// Admin: one student's account in full (money, shares, orders, ledger).

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api";
import { dateTimeText, money, percent, pnlClass } from "../../format";

export default function UserDetail() {
  const { id } = useParams();
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api(`/admin/users/${id}`).then(setDetail).catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="page"><div className="message error">{error}</div></div>;
  if (!detail) return <div className="page">Loading...</div>;

  const { user, portfolio, orders, transactions } = detail;

  return (
    <div className="page stack">
      <div className="page-head">
        <Link to="/admin/users">← All users</Link>
        <h1>{user.name}</h1>
        <div className="muted">{user.email}</div>
      </div>

      {portfolio && (
        <>
          <div className="grid-4">
            <div className="card stat"><div className="label">Cash</div><div className="value">{money(portfolio.cash)}</div></div>
            <div className="card stat"><div className="label">Total value</div><div className="value">{money(portfolio.total_value)}</div></div>
            <div className="card stat"><div className="label">Money received</div><div className="value">{money(portfolio.capital)}</div></div>
            <div className="card stat">
              <div className="label">Profit / loss</div>
              <div className={`value ${pnlClass(portfolio.total_pnl)}`}>{money(portfolio.total_pnl)} ({percent(portfolio.total_pnl_pct)})</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2>Holdings</h2>
              {portfolio.holdings.length === 0 && <div className="muted">No shares.</div>}
              <table>
                <tbody>
                  {portfolio.holdings.map((h) => (
                    <tr key={h.symbol}>
                      <td>{h.symbol}</td>
                      <td className="num">{h.quantity} @ {money(h.avg_price)}</td>
                      <td className={`num ${pnlClass(h.pnl)}`}>{money(h.pnl)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="card">
              <h2>Wallet ledger</h2>
              <div className="scroll">
                <table>
                  <tbody>
                    {transactions.map((t) => (
                      <tr key={t.id}>
                        <td>{dateTimeText(t.created_at)}</td>
                        <td className="muted">{t.kind}</td>
                        <td className={`num ${pnlClass(t.amount)}`}>{money(t.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Recent orders</h2>
            {orders.length === 0 && <div className="muted">No orders.</div>}
            <table>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td>{dateTimeText(o.created_at)}</td>
                    <td><span className={o.side === "BUY" ? "green" : "red"}>{o.side}</span> {o.quantity} {o.symbol}</td>
                    <td className="muted">{o.order_type}</td>
                    <td className="num">{o.fill_price ? money(o.fill_price) : "-"}</td>
                    <td><span className="badge">{o.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
