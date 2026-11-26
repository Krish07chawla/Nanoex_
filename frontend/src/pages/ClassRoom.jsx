// The live class room. The trader posts notes, students watch and ask questions.
// New notes and questions arrive through a WebSocket, so nobody needs to refresh.

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getToken } from "../api";
import { useAuth } from "../auth";
import PriceChart from "../components/PriceChart";
import { dateTimeText, money, pnlClass, percent } from "../format";
import { useLive } from "../live";

const KIND_TEXT = { NOTE: "Note", BUY_IDEA: "Buy idea", SELL_IDEA: "Sell idea" };
const KIND_BADGE = { NOTE: "", BUY_IDEA: "green", SELL_IDEA: "red" };

export default function ClassRoom() {
  const { id } = useParams();
  const { user } = useAuth();
  const { prices } = useLive();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [symbol, setSymbol] = useState(null);

  const isOwner = data && user.id === data.trader_id;
  const isStudent = user.role === "STUDENT";

  const load = () =>
    api(`/classes/${id}`)
      .then((d) => {
        setData(d);
        setSymbol((current) => current || d.symbols[0]);
      })
      .catch((err) => setError(err.message));

  useEffect(() => {
    load();
  }, [id]);

  // Live events for this class (notes, questions, answers, start / end)
  useEffect(() => {
    let socket;
    let timer;
    let stopped = false;

    function connect() {
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${scheme}://${window.location.host}/ws?token=${getToken()}&class_id=${id}`);
      socket.onmessage = (event) => {
        const m = JSON.parse(event.data);
        setData((d) => {
          if (!d) return d;
          if (m.type === "note") return { ...d, notes: [...d.notes, m.note] };
          if (m.type === "question") return { ...d, questions: [...d.questions, m.question] };
          if (m.type === "answer") return { ...d, questions: d.questions.map((q) => (q.id === m.question.id ? m.question : q)) };
          if (m.type === "status") return { ...d, status: m.status };
          return d;
        });
      };
      socket.onclose = () => {
        if (!stopped) timer = setTimeout(connect, 3000);
      };
    }
    connect();
    return () => {
      stopped = true;
      clearTimeout(timer);
      if (socket) socket.close();
    };
  }, [id]);

  if (error) return <div className="page"><div className="message error">{error}</div></div>;
  if (!data) return <div className="page">Loading...</div>;

  const quote = prices[symbol];
  const change = quote ? ((quote.price - quote.prev_close) / quote.prev_close) * 100 : 0;

  async function changeStatus(action) {
    try {
      await api(`/classes/${id}/${action}`, { method: "POST" });
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page stack">
      <div className="spread">
        <div>
          <h1>{data.title}</h1>
          <div className="muted">
            Trader: {data.trader} · {data.students} {data.students === 1 ? "student" : "students"} · Join code: <span className="code" style={{ fontSize: 14 }}>{data.code}</span>
          </div>
        </div>
        <div className="row">
          <span className={`badge ${data.status === "LIVE" ? "green" : ""}`}>{data.status}</span>
          {isOwner && data.status === "SCHEDULED" && <button className="primary" onClick={() => changeStatus("start")}>Start class</button>}
          {isOwner && data.status === "LIVE" && <button className="sell" onClick={() => changeStatus("end")}>End class</button>}
          {data.status === "ENDED" && <Link to={`/classes/${id}/replay`}><button>Watch replay</button></Link>}
        </div>
      </div>

      <div className="grid-class">
        <div className="card">
          <div className="tabs">
            {data.symbols.map((s) => (
              <button key={s} className={s === symbol ? "on" : ""} onClick={() => setSymbol(s)}>{s}</button>
            ))}
          </div>
          <div className="spread">
            <h2>{symbol}</h2>
            <div className="right">
              <b style={{ fontSize: 22 }}>{quote ? money(quote.price) : "..."}</b>{" "}
              <span className={pnlClass(change)}>{percent(change)}</span>
            </div>
          </div>
          <PriceChart symbol={symbol} height={340} />
        </div>

        <div className="stack">
          <TraderNotes data={data} isOwner={isOwner} classId={id} />
          <Questions data={data} isOwner={isOwner} isStudent={isStudent} classId={id} />
          {isStudent && <MyNotes data={data} classId={id} reload={load} />}
        </div>
      </div>
    </div>
  );
}

function TraderNotes({ data, isOwner, classId }) {
  const [text, setText] = useState("");
  const [kind, setKind] = useState("NOTE");
  const [noteSymbol, setNoteSymbol] = useState(data.symbols[0]);
  const [error, setError] = useState("");

  async function post(event) {
    event.preventDefault();
    setError("");
    try {
      await api(`/classes/${classId}/notes`, { method: "POST", body: { text, kind, symbol: noteSymbol } });
      setText("");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card stack">
      <h2>Trader's notes</h2>
      {isOwner && (
        <form className="stack" onSubmit={post}>
          <div className="row">
            <select style={{ width: 120 }} value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="NOTE">Note</option>
              <option value="BUY_IDEA">Buy idea</option>
              <option value="SELL_IDEA">Sell idea</option>
            </select>
            <select style={{ width: 130 }} value={noteSymbol} onChange={(e) => setNoteSymbol(e.target.value)}>
              {data.symbols.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Explain what you see on the chart..." required />
          <button className="primary" disabled={data.status !== "LIVE"}>Post to class</button>
          {data.status !== "LIVE" && <div className="muted">Start the class to post notes.</div>}
          {error && <div className="message error">{error}</div>}
        </form>
      )}
      <div className="scroll">
        {data.notes.length === 0 && <div className="muted">No notes yet.</div>}
        {[...data.notes].reverse().map((n) => (
          <div className="list-item" key={n.id}>
            <span className={`badge ${KIND_BADGE[n.kind]}`}>{KIND_TEXT[n.kind]}</span>{" "}
            <b>{n.symbol}</b> {n.price && <span className="muted">at {money(n.price)}</span>}
            <div>{n.text}</div>
            <div className="muted">{dateTimeText(n.created_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Questions({ data, isOwner, isStudent, classId }) {
  const [text, setText] = useState("");
  const [answers, setAnswers] = useState({});

  async function ask(event) {
    event.preventDefault();
    await api(`/classes/${classId}/questions`, { method: "POST", body: { text } });
    setText("");
  }

  async function answer(questionId) {
    await api(`/questions/${questionId}/answer`, { method: "POST", body: { text: answers[questionId] } });
    setAnswers({ ...answers, [questionId]: "" });
  }

  return (
    <div className="card stack">
      <h2>Questions</h2>
      {isStudent && (
        <form className="row" onSubmit={ask}>
          <input style={{ flex: 1 }} value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask the trader..." required />
          <button className="primary">Ask</button>
        </form>
      )}
      <div className="scroll">
        {data.questions.length === 0 && <div className="muted">No questions yet.</div>}
        {[...data.questions].reverse().map((q) => (
          <div className="list-item" key={q.id}>
            <b>{q.student}:</b> {q.text}
            {q.answer && <div className="message ok" style={{ marginTop: 6 }}>Trader: {q.answer}</div>}
            {!q.answer && isOwner && (
              <div className="row" style={{ marginTop: 6 }}>
                <input style={{ flex: 1 }} value={answers[q.id] || ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} placeholder="Your answer" />
                <button className="small" onClick={() => answer(q.id)}>Reply</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function MyNotes({ data, classId, reload }) {
  const [text, setText] = useState("");

  async function save(event) {
    event.preventDefault();
    await api(`/classes/${classId}/my-notes`, { method: "POST", body: { text } });
    setText("");
    reload();
  }

  return (
    <div className="card stack">
      <h2>My private notes</h2>
      <form className="stack" onSubmit={save}>
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Write what you learned..." required />
        <button>Save note</button>
      </form>
      {data.my_notes.map((n) => (
        <div className="list-item" key={n.id}>
          {n.text}
          <div className="muted">{dateTimeText(n.created_at)}</div>
        </div>
      ))}
    </div>
  );
}
