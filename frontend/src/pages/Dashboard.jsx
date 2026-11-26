// Student home: money summary, watchlist and latest orders.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { money, percent, pnlClass } from "../format";
import { useLive } from "../live";

function Stat({ label, value, className = "" }) {
  return (
    <div className="card stat">
      <div className="label">{label}</div>
      <div className={`value ${className}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const { prices, stocks } = useLive();
  const [portfolio, setPortfolio] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    api("/portfolio").then(setPortfolio);
    api("/watchlist").then(setWatchlist);
    api("/orders").then((all) => setOrders(all.slice(0, 5)));
  }, []);

  if (!portfolio) return <div className="page">Loading...</div>;
  const nameOf = (symbol) => stocks.find((s) => s.symbol === symbol)?.name || "";

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Dashboard</h1>
        <div className="muted">Your virtual trading account</div>
      </div>

      {portfolio.capital === 0 && (
        <div className="message info">
          You have no virtual money yet. Ask your admin to send you some, then you can start trading.
        </div>
      )}

      <div className="grid-4">
        <Stat label="Cash available" value={money(portfolio.cash)} />
        <Stat label="Shares value" value={money(portfolio.holdings_value)} />
        <Stat label="Total value" value={money(portfolio.total_value)} />
        <Stat
          label="Overall profit / loss"
          value={`${money(portfolio.total_pnl)} (${percent(portfolio.total_pnl_pct)})`}
          className={pnlClass(portfolio.total_pnl)}
        />
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="spread">
            <h2>My watchlist</h2>
            <Link to="/market">Add stocks</Link>
          </div>
          {watchlist.length === 0 && <div className="muted">Star a stock on the Market page to see it here.</div>}
          <table>
            <tbody>
              {watchlist.map((symbol) => {
                const quote = prices[symbol];
                const change = quote ? ((quote.price - quote.prev_close) / quote.prev_close) * 100 : 0;
                return (
                  <tr key={symbol}>
                    <td>
                      <Link to={`/market?symbol=${symbol}`}>{symbol}</Link>
                      <div className="muted">{nameOf(symbol)}</div>
                    </td>
                    <td className="num">{quote ? money(quote.price) : "..."}</td>
                    <td className={`num ${pnlClass(change)}`}>{percent(change)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="spread">
            <h2>Latest orders</h2>
            <Link to="/orders">See all</Link>
          </div>
          {orders.length === 0 && <div className="muted">No orders yet.</div>}
          <table>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>
                    <span className={o.side === "BUY" ? "green" : "red"}>{o.side}</span> {o.quantity} {o.symbol}
                  </td>
                  <td className="num">{o.fill_price ? money(o.fill_price) : "-"}</td>
                  <td className="num">
                    <span className="badge">{o.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card row">
        <div style={{ flex: 1 }}>
          <h2>Need a trade idea?</h2>
          <div className="muted">The AI advisor looks at your trading history and the market and suggests trades to learn from.</div>
        </div>
        <Link to="/advisor">
          <button className="primary">Ask the AI advisor</button>
        </Link>
      </div>
    </div>
  );
}
