// Replay of a finished class: drag the slider to travel through the lesson.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { clockText, dateTimeText, money, toDate } from "../format";

const KIND_TEXT = { NOTE: "Note", BUY_IDEA: "Buy idea", SELL_IDEA: "Sell idea" };

export default function Replay() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [symbol, setSymbol] = useState(null);
  const [position, setPosition] = useState(0);

  useEffect(() => {
    api(`/classes/${id}/replay`)
      .then((d) => {
        setData(d);
        setSymbol(d.class.symbols[0]);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="page"><div className="message error">{error}</div></div>;
  if (!data) return <div className="page">Loading...</div>;

  const points = data.ticks
    .filter((t) => t.symbol === symbol)
    .map((t) => ({ time: toDate(t.time).getTime(), price: t.price }));
  const shown = points.slice(0, position || points.length);
  const now = shown.length ? shown[shown.length - 1].time : 0;
  const notes = data.notes.filter((n) => toDate(n.created_at).getTime() <= now);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Replay: {data.class.title}</h1>
        <div className="muted">Trader: {data.class.trader} · {dateTimeText(data.class.started_at)}</div>
      </div>

      {points.length === 0 ? (
        <div className="card muted">No prices were saved for this class. Prices are saved only while a class is live.</div>
      ) : (
        <div className="grid-class">
          <div className="card">
            <div className="tabs">
              {data.class.symbols.map((s) => (
                <button key={s} className={s === symbol ? "on" : ""} onClick={() => { setSymbol(s); setPosition(0); }}>{s}</button>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={shown}>
                <CartesianGrid stroke="#f0f0f0" />
                <XAxis dataKey="time" type="number" domain={[points[0].time, points[points.length - 1].time]} tickFormatter={clockText} fontSize={12} />
                <YAxis domain={["auto", "auto"]} width={70} tickFormatter={(v) => v.toFixed(0)} fontSize={12} />
                <Tooltip labelFormatter={clockText} formatter={(v) => [money(v), "Price"]} />
                <Line type="monotone" dataKey="price" stroke="#2563eb" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
            <input type="range" min="1" max={points.length} value={position || points.length} onChange={(e) => setPosition(Number(e.target.value))} />
            <div className="muted">Time in class: {now ? clockText(now) : "-"}</div>
          </div>

          <div className="card">
            <h2>Notes so far</h2>
            <div className="scroll">
              {notes.length === 0 && <div className="muted">No notes yet at this point.</div>}
              {notes.map((n) => (
                <div className="list-item" key={n.id}>
                  <span className="badge">{KIND_TEXT[n.kind]}</span> <b>{n.symbol}</b> {n.price && <span className="muted">at {money(n.price)}</span>}
                  <div>{n.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
