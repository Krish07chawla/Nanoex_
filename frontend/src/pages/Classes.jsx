// Class list. Traders create classes, students join with a code.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { dateTimeText } from "../format";
import { useLive } from "../live";

const STATUS_BADGE = { SCHEDULED: "", LIVE: "green", ENDED: "" };

function CreateClass({ onCreated }) {
  const { stocks } = useLive();
  const [title, setTitle] = useState("");
  const [symbols, setSymbols] = useState([]);
  const [error, setError] = useState("");

  const toggle = (symbol) =>
    setSymbols(symbols.includes(symbol) ? symbols.filter((s) => s !== symbol) : [...symbols, symbol]);

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/classes", { method: "POST", body: { title, symbols } });
      setTitle("");
      setSymbols([]);
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h2>Create a class</h2>
      <div>
        <label>Title</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Today: reading bank stocks" required />
      </div>
      <div>
        <label>Stocks to teach on (pick up to 6)</label>
        <div className="row">
          {stocks.map((s) => (
            <label key={s.symbol} style={{ display: "flex", gap: 4, alignItems: "center", margin: 0 }}>
              <input type="checkbox" style={{ width: "auto" }} checked={symbols.includes(s.symbol)} onChange={() => toggle(s.symbol)} />
              {s.symbol}
            </label>
          ))}
        </div>
      </div>
      {error && <div className="message error">{error}</div>}
      <button className="primary" disabled={symbols.length === 0 || symbols.length > 6}>Create class</button>
    </form>
  );
}

function JoinClass({ onJoined }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/classes/join", { method: "POST", body: { code: code.toUpperCase() } });
      setCode("");
      onJoined();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h2>Join a class</h2>
      <div className="row">
        <input style={{ width: 160 }} value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} placeholder="6-letter code" required />
        <button className="primary">Join</button>
      </div>
      {error && <div className="message error">{error}</div>}
    </form>
  );
}

export default function Classes() {
  const { user } = useAuth();
  const [classes, setClasses] = useState([]);

  const load = () => api("/classes").then(setClasses);
  useEffect(() => {
    load();
  }, []);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>{user.role === "TRADER" ? "My classes" : "Classes"}</h1>
        <div className="muted">Live lessons on today's market prices</div>
      </div>

      {user.role === "TRADER" && <CreateClass onCreated={load} />}
      {user.role === "STUDENT" && <JoinClass onJoined={load} />}

      <div className="card">
        {classes.length === 0 && <div className="muted">No classes yet.</div>}
        <table>
          <thead>
            <tr><th>Title</th><th>Trader</th><th>Stocks</th><th>Status</th>{user.role !== "STUDENT" && <th>Join code</th>}<th className="num">Students</th><th></th></tr>
          </thead>
          <tbody>
            {classes.map((c) => (
              <tr key={c.id}>
                <td>{c.title}<div className="muted">{dateTimeText(c.started_at)}</div></td>
                <td>{c.trader}</td>
                <td className="muted">{c.symbols.join(", ")}</td>
                <td><span className={`badge ${STATUS_BADGE[c.status]}`}>{c.status}</span></td>
                {user.role !== "STUDENT" && <td className="code">{c.code}</td>}
                <td className="num">{c.students}</td>
                <td className="num">
                  <Link to={`/classes/${c.id}`}><button className="small primary">Open</button></Link>{" "}
                  {c.status === "ENDED" && <Link to={`/classes/${c.id}/replay`}><button className="small">Replay</button></Link>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
