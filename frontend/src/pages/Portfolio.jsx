// What the student owns, with live profit and loss.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { money, percent, pnlClass } from "../format";
import { useLive } from "../live";

export default function Portfolio() {
  const { prices } = useLive();
  const [portfolio, setPortfolio] = useState(null);

  useEffect(() => {
    api("/portfolio").then(setPortfolio);
  }, []);

  if (!portfolio) return <div className="page">Loading...</div>;

  // Use the newest live price so profit and loss move on screen
  const rows = portfolio.holdings.map((h) => {
    const price = prices[h.symbol]?.price ?? h.price;
    const value = price * h.quantity;
    const pnl = value - h.avg_price * h.quantity;
    return { ...h, price, value, pnl, pnl_pct: (pnl / (h.avg_price * h.quantity)) * 100 };
  });
  const totalValue = rows.reduce((sum, r) => sum + r.value, 0);
  const totalPnl = rows.reduce((sum, r) => sum + r.pnl, 0);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Portfolio</h1>
        <div className="muted">Your shares, valued at live prices</div>
      </div>

      <div className="grid-4">
        <div className="card stat"><div className="label">Cash</div><div className="value">{money(portfolio.cash)}</div></div>
        <div className="card stat"><div className="label">Shares value</div><div className="value">{money(totalValue)}</div></div>
        <div className="card stat">
          <div className="label">Unrealised profit / loss</div>
          <div className={`value ${pnlClass(totalPnl)}`}>{money(totalPnl)}</div>
        </div>
        <div className="card stat">
          <div className="label">Profit already booked</div>
          <div className={`value ${pnlClass(portfolio.realized_pnl)}`}>{money(portfolio.realized_pnl)}</div>
        </div>
      </div>

      <div className="card">
        <h2>Holdings</h2>
        {rows.length === 0 && <div className="muted">You do not own any shares yet. Go to the Market page to buy.</div>}
        {rows.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Stock</th><th className="num">Qty</th><th className="num">Avg price</th><th className="num">Live price</th>
                <th className="num">Value</th><th className="num">Profit / loss</th><th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.symbol}>
                  <td>{r.symbol}<div className="muted">{r.name}</div></td>
                  <td className="num">{r.quantity}</td>
                  <td className="num">{money(r.avg_price)}</td>
                  <td className="num">{money(r.price)}</td>
                  <td className="num">{money(r.value)}</td>
                  <td className={`num ${pnlClass(r.pnl)}`}>{money(r.pnl)} ({percent(r.pnl_pct)})</td>
                  <td className="num"><Link to={`/market?symbol=${r.symbol}`}><button className="small">Trade</button></Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
