// A line chart of one stock: today's history, then live points are added.

import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { clockText, money, toDate } from "../format";
import { useLive } from "../live";

export default function PriceChart({ symbol, height = 320 }) {
  const { prices } = useLive();
  const [points, setPoints] = useState([]); // [{time (ms), price}]

  // Load today's history when the stock changes
  useEffect(() => {
    let active = true;
    setPoints([]);
    api(`/market/history/${symbol}`)
      .then((data) => {
        if (active) setPoints(data.points.map((p) => ({ time: toDate(p.time).getTime(), price: p.price })));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [symbol]);

  // Add a point every time the live price changes
  const live = prices[symbol]?.price;
  useEffect(() => {
    if (live === undefined) return;
    setPoints((old) => [...old.slice(-400), { time: Date.now(), price: live }]);
  }, [live]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={points} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid stroke="#f0f0f0" />
        <XAxis dataKey="time" type="number" domain={["dataMin", "dataMax"]} tickFormatter={clockText} fontSize={12} />
        <YAxis domain={["auto", "auto"]} width={70} tickFormatter={(v) => v.toFixed(0)} fontSize={12} />
        <Tooltip labelFormatter={clockText} formatter={(value) => [money(value), "Price"]} />
        <Line type="monotone" dataKey="price" stroke="#2563eb" dot={false} strokeWidth={2} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
