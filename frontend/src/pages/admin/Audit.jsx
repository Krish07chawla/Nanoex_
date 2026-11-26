// Admin: a list of everything the admin did (money moved, accounts disabled).

import { useEffect, useState } from "react";
import { api } from "../../api";
import { dateTimeText } from "../../format";

export default function Audit() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api("/admin/audit").then(setRows);
  }, []);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Audit log</h1>
        <div className="muted">Every important admin action is saved here.</div>
      </div>
      <div className="card">
        {rows.length === 0 && <div className="muted">Nothing yet.</div>}
        <table>
          <thead>
            <tr><th>Time</th><th>Action</th><th>Details</th></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{dateTimeText(r.created_at)}</td>
                <td><span className="badge">{r.action}</span></td>
                <td>{r.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
