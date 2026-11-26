// Students ranked by their percentage return.

import { useEffect, useState } from "react";
import { api } from "../api";
import { money, percent, pnlClass } from "../format";

export default function Leaderboard() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api("/leaderboard").then(setRows);
  }, []);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Leaderboard</h1>
        <div className="muted">Return on the virtual money each student was given.</div>
      </div>
      <div className="card">
        {rows.length === 0 && <div className="muted">No students with money yet.</div>}
        <table>
          <thead>
            <tr><th>Rank</th><th>Student</th><th className="num">Total value</th><th className="num">Return</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.rank}>
                <td>{r.rank}</td>
                <td>{r.name}</td>
                <td className="num">{money(r.total_value)}</td>
                <td className={`num ${pnlClass(r.return_pct)}`}>{percent(r.return_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
