// Market page: stock list, live chart, order ticket, watchlist stars and price alerts.

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import OrderTicket from "../components/OrderTicket";
import PriceChart from "../components/PriceChart";
import { money, percent, pnlClass } from "../format";
import { useLive } from "../live";

function AlertBox({ symbol }) {
  const [alerts, setAlerts] = useState([]);
  const [direction, setDirection] = useState("ABOVE");
  const [price, setPrice] = useState("");

  const load = () => api("/alerts").then(setAlerts);
  useEffect(() => {
    load();
  }, []);

  async function add(event) {
    event.preventDefault();
    await api("/alerts", { method: "POST", body: { symbol, direction, price: Number(price) } });
    setPrice("");
    load();
  }

  async function remove(id) {
    await api(`/alerts/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="card stack">
      <h3>Price alert for {symbol}</h3>
      <form className="row" onSubmit={add}>
        <select style={{ width: 90 }} value={direction} onChange={(e) => setDirection(e.target.value)}>
          <option value="ABOVE">above</option>
          <option value="BELOW">below</option>
        </select>
        <input style={{ width: 90 }} type="number" step="0.05" value={price} onChange={(e) => setPrice(e.target.value)} required />
        <button className="small">Add</button>
      </form>
      {alerts.slice(0, 5).map((a) => (
        <div className="spread muted" key={a.id}>
          <span>
            {a.symbol} {a.direction.toLowerCase()} {money(a.price)} {a.triggered && <span className="badge green">fired</span>}
          </span>
          <button className="small" onClick={() => remove(a.id)}>
            x
          </button>
        </div>
      ))}
    </div>
  );
}

export default function Market() {
  const { user } = useAuth();
  const { prices, stocks } = useLive();
  const [params] = useSearchParams();
  const [symbol, setSymbol] = useState(params.get("symbol") || "RELIANCE");
  const [watchlist, setWatchlist] = useState([]);
  const isStudent = user.role === "STUDENT";

  // An idea from the AI advisor comes in through the web address
  const prefill = params.get("side")
    ? {
        symbol: params.get("symbol"),
        side: params.get("side"),
        quantity: Number(params.get("qty") || 1),
        stop_loss: params.get("stop") ? Number(params.get("stop")) : null,
      }
    : null;

  useEffect(() => {
    if (isStudent) api("/watchlist").then(setWatchlist);
  }, [isStudent]);

  async function toggleStar(event, stock) {
    event.stopPropagation();
    if (watchlist.includes(stock)) {
      await api(`/watchlist/${stock}`, { method: "DELETE" });
      setWatchlist(watchlist.filter((s) => s !== stock));
    } else {
      await api("/watchlist", { method: "POST", body: { symbol: stock } });
      setWatchlist([...watchlist, stock]);
    }
  }

  const quote = prices[symbol];
  const change = quote ? ((quote.price - quote.prev_close) / quote.prev_close) * 100 : 0;
  const name = stocks.find((s) => s.symbol === symbol)?.name;

  return (
    <div className="page">
      <div className="grid-market">
        <div className="card">
          <h2>Stocks (NSE)</h2>
          <table>
            <tbody>
              {stocks.map((stock) => {
                const q = prices[stock.symbol];
                const c = q ? ((q.price - q.prev_close) / q.prev_close) * 100 : 0;
                return (
                  <tr
                    key={stock.symbol}
                    className={`clickable ${stock.symbol === symbol ? "selected" : ""}`}
                    onClick={() => setSymbol(stock.symbol)}
                  >
                    {isStudent && (
                      <td style={{ width: 22 }} onClick={(e) => toggleStar(e, stock.symbol)}>
                        {watchlist.includes(stock.symbol) ? "★" : "☆"}
                      </td>
                    )}
                    <td>{stock.symbol}</td>
                    <td className="num">
                      {q ? q.price.toFixed(2) : "..."}
                      <div className={`muted ${pnlClass(c)}`}>{percent(c)}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="spread">
            <div>
              <h1>{symbol}</h1>
              <div className="muted">{name}</div>
            </div>
            <div className="right">
              <div style={{ fontSize: 24, fontWeight: 600 }}>{quote ? money(quote.price) : "..."}</div>
              <div className={pnlClass(change)}>{percent(change)} today</div>
            </div>
          </div>
          <PriceChart symbol={symbol} />
        </div>

        <div className="stack">
          {isStudent ? (
            <>
              <OrderTicket symbol={symbol} prefill={prefill} />
              <AlertBox symbol={symbol} />
            </>
          ) : (
            <div className="card muted">Only students can place trades. Traders teach in live classes.</div>
          )}
        </div>
      </div>
    </div>
  );
}
