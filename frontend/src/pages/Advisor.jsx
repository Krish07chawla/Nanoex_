// AI advisor: asks the backend for trade ideas and lets the student try one.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { money } from "../format";

export default function Advisor() {
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask() {
    setLoading(true);
    setError("");
    try {
      setResult(await api("/advisor/suggestions", { method: "POST" }));
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }

  // Open the Market page with the order form already filled in
  function tryIdea(idea) {
    const stop = idea.stop_loss ? `&stop=${idea.stop_loss}` : "";
    navigate(`/market?symbol=${idea.symbol}&side=${idea.side}&qty=${idea.quantity}${stop}`);
  }

  return (
    <div className="page stack">
      <div className="spread">
        <div>
          <h1>AI Advisor</h1>
          <div className="muted">Trade ideas based on your own history and the live market.</div>
        </div>
        <button className="primary" onClick={ask} disabled={loading}>
          {loading ? "Thinking..." : "Get trade ideas"}
        </button>
      </div>

      <div className="message info">
        For learning only. These ideas and outlooks are estimates, they can be wrong, and they are not financial advice.
      </div>
      {error && <div className="message error">{error}</div>}

      {result && (
        <>
          <div className="card">
            <div className="row">
              <span className={`badge ${result.source === "grok" ? "blue" : ""}`}>
                {result.source === "grok" ? "Made by Grok AI" : "Made by the rule-based advisor"}
              </span>
              {result.note && <span className="muted">{result.note}</span>}
            </div>
            <p style={{ marginBottom: 0 }}><b>About your trading:</b> {result.insight}</p>
          </div>

          {result.suggestions.length === 0 && (
            <div className="card muted">No clear ideas right now. Check again after prices move, or make sure you have cash or shares.</div>
          )}

          <div className="grid-2">
            {result.suggestions.map((idea) => (
              <div className="card stack" key={idea.id}>
                <div className="spread">
                  <h2 style={{ margin: 0 }}>
                    <span className={idea.side === "BUY" ? "green" : "red"}>{idea.side}</span> {idea.quantity} × {idea.symbol}
                  </h2>
                  <span className="badge">{idea.confidence} confidence</span>
                </div>
                <div><b>Outlook:</b> {idea.outlook}</div>
                <div>{idea.reason}</div>
                {idea.stop_loss && <div className="muted">Suggested stop-loss: {money(idea.stop_loss)}</div>}
                <button onClick={() => tryIdea(idea)}>Try this idea on the Market page</button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
