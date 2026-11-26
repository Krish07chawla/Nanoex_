// Admin: see every account and send virtual money to students.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import { money, pnlClass } from "../../format";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [filter, setFilter] = useState("STUDENT");
  const [selected, setSelected] = useState([]);
  const [form, setForm] = useState({ kind: "CREDIT", amount: "", note: "", all: false });
  const [message, setMessage] = useState(null);

  const load = () => api("/admin/users").then(setUsers);
  useEffect(() => {
    load();
  }, []);

  const shown = users.filter((u) => u.role === filter);

  const toggle = (id) => setSelected(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);

  async function sendMoney(event) {
    event.preventDefault();
    setMessage(null);
    try {
      const result = await api("/admin/wallet", {
        method: "POST",
        body: {
          kind: form.kind,
          amount: Number(form.amount),
          note: form.note,
          all_students: form.all,
          user_ids: form.all ? [] : selected,
        },
      });
      setMessage({ ok: true, text: `Done for ${result.students} student(s).` });
      setForm({ ...form, amount: "", note: "" });
      load();
    } catch (err) {
      setMessage({ ok: false, text: err.message });
    }
  }

  async function setActive(user, isActive) {
    await api(`/admin/users/${user.id}/active`, { method: "PATCH", body: { is_active: isActive } });
    load();
  }

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Users</h1>
        <div className="muted">See every account and give students virtual money to learn with.</div>
      </div>

      <form className="card stack" onSubmit={sendMoney}>
        <h2>Send virtual money</h2>
        <div className="row">
          <select style={{ width: 170 }} value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            <option value="CREDIT">Send money</option>
            <option value="DEBIT">Take money back</option>
          </select>
          <input style={{ width: 150 }} type="number" min="1" placeholder="Amount (₹)" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          <input style={{ flex: 1, minWidth: 180 }} placeholder="Note (for example: Week 1 practice money)" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
        </div>
        <div className="row">
          <label style={{ display: "flex", gap: 6, alignItems: "center", margin: 0 }}>
            <input type="checkbox" style={{ width: "auto" }} checked={form.all} onChange={(e) => setForm({ ...form, all: e.target.checked })} />
            All students
          </label>
          <span className="muted">{form.all ? "Applies to every active student" : `${selected.length} student(s) selected in the table below`}</span>
        </div>
        <div><button className="primary" disabled={!form.all && selected.length === 0}>Apply</button></div>
        {message && <div className={`message ${message.ok ? "ok" : "error"}`}>{message.text}</div>}
      </form>

      <div className="card">
        <div className="tabs">
          {["STUDENT", "TRADER", "ADMIN"].map((role) => (
            <button key={role} className={filter === role ? "on" : ""} onClick={() => setFilter(role)}>{role.charAt(0) + role.slice(1).toLowerCase()}s</button>
          ))}
        </div>
        <table>
          <thead>
            <tr>
              {filter === "STUDENT" && <th></th>}
              <th>Name</th><th>Email</th>
              {filter === "STUDENT" && <><th className="num">Cash</th><th className="num">Total value</th><th className="num">Profit / loss</th></>}
              <th>Status</th><th></th>
            </tr>
          </thead>
          <tbody>
            {shown.map((u) => (
              <tr key={u.id}>
                {filter === "STUDENT" && <td><input type="checkbox" style={{ width: "auto" }} checked={selected.includes(u.id)} onChange={() => toggle(u.id)} /></td>}
                <td>{u.name}</td>
                <td className="muted">{u.email}</td>
                {filter === "STUDENT" && (
                  <>
                    <td className="num">{money(u.cash)}</td>
                    <td className="num">{money(u.total_value)}</td>
                    <td className={`num ${pnlClass(u.total_pnl)}`}>{money(u.total_pnl)}</td>
                  </>
                )}
                <td><span className={`badge ${u.is_active ? "green" : "red"}`}>{u.is_active ? "Active" : "Disabled"}</span></td>
                <td className="num">
                  {filter === "STUDENT" && <Link to={`/admin/users/${u.id}`}><button className="small">Open</button></Link>}{" "}
                  {u.role !== "ADMIN" && <button className="small" onClick={() => setActive(u, !u.is_active)}>{u.is_active ? "Disable" : "Enable"}</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
