// The buy / sell form (market, limit and stop-loss orders).

import { useEffect, useState } from "react";
import { api } from "../api";
import { money } from "../format";
import { useLive } from "../live";

export default function OrderTicket({ symbol, prefill, onDone }) {
  const { prices } = useLive();
  const price = prices[symbol]?.price;

  const [side, setSide] = useState("BUY");
  const [type, setType] = useState("MARKET");
  const [quantity, setQuantity] = useState(1);
  const [limit, setLimit] = useState("");
  const [message, setMessage] = useState(null); // {text, ok}
  const [busy, setBusy] = useState(false);

  // An idea from the AI advisor fills the form for us
  useEffect(() => {
    if (!prefill) return;
    setSide(prefill.side);
    setQuantity(prefill.quantity);
    if (prefill.stop_loss) setLimit(prefill.stop_loss);
  }, [prefill]);

  // Stop-loss is only for selling
  useEffect(() => {
    if (side === "BUY" && type === "STOP_LOSS") setType("MARKET");
  }, [side, type]);

  const unitPrice = type === "MARKET" ? price : Number(limit);
  const estimate = unitPrice ? unitPrice * Number(quantity || 0) : 0;

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const order = await api("/orders", {
        method: "POST",
        body: {
          symbol,
          side,
          order_type: type,
          quantity: Number(quantity),
          limit_price: type === "MARKET" ? null : Number(limit),
          source: prefill && prefill.symbol === symbol ? "AI" : "MANUAL",
        },
      });
      const text =
        order.status === "FILLED"
          ? `Done: ${side} ${order.quantity} ${symbol} at ${money(order.fill_price)}`
          : "Order placed. It will fill when the price is reached.";
      setMessage({ text, ok: true });
      if (onDone) onDone();
    } catch (error) {
      setMessage({ text: error.message, ok: false });
    }
    setBusy(false);
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h2>
        {symbol} <span className="muted">{price ? money(price) : "..."}</span>
      </h2>

      <div className="tabs">
        <button type="button" className={side === "BUY" ? "on" : ""} onClick={() => setSide("BUY")}>
          Buy
        </button>
        <button type="button" className={side === "SELL" ? "on" : ""} onClick={() => setSide("SELL")}>
          Sell
        </button>
      </div>

      <div>
        <label>Order type</label>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="MARKET">Market (now, at live price)</option>
          <option value="LIMIT">Limit (at my price)</option>
          {side === "SELL" && <option value="STOP_LOSS">Stop-loss (sell if price falls)</option>}
        </select>
      </div>

      <div>
        <label>Quantity</label>
        <input type="number" min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
      </div>

      {type !== "MARKET" && (
        <div>
          <label>{type === "LIMIT" ? "Limit price (₹)" : "Trigger price (₹)"}</label>
          <input type="number" step="0.05" min="0" value={limit} onChange={(e) => setLimit(e.target.value)} />
        </div>
      )}

      <div className="muted">Estimated value: {money(estimate)} (plus small brokerage)</div>

      <button className={`full ${side === "BUY" ? "buy" : "sell"}`} disabled={busy || !price}>
        {side === "BUY" ? "Buy" : "Sell"} {symbol}
      </button>

      {message && <div className={`message ${message.ok ? "ok" : "error"}`}>{message.text}</div>}
    </form>
  );
}
