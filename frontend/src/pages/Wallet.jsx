// Virtual wallet: balance and every credit or debit.

import { useEffect, useState } from "react";
import { api } from "../api";
import { dateTimeText, money, pnlClass } from "../format";

const KIND_TEXT = {
  ADMIN_CREDIT: "Money from admin",
  ADMIN_DEBIT: "Taken back by admin",
  TRADE_BUY: "Bought shares",
  TRADE_SELL: "Sold shares",
};

export default function Wallet() {
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    api("/wallet").then(setWallet);
  }, []);

  if (!wallet) return <div className="page">Loading...</div>;

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Wallet</h1>
        <div className="muted">Virtual money only. Your admin sends you money to practise with.</div>
      </div>

      <div className="grid-4">
        <div className="card stat"><div className="label">Balance</div><div className="value">{money(wallet.balance)}</div></div>
        <div className="card stat"><div className="label">Total money received</div><div className="value">{money(wallet.capital)}</div></div>
      </div>

      <div className="card">
        <h2>History</h2>
        {wallet.transactions.length === 0 && <div className="muted">No transactions yet.</div>}
        <table>
          <thead>
            <tr><th>Time</th><th>What</th><th>Note</th><th className="num">Amount</th><th className="num">Balance after</th></tr>
          </thead>
          <tbody>
            {wallet.transactions.map((t) => (
              <tr key={t.id}>
                <td>{dateTimeText(t.created_at)}</td>
                <td>{KIND_TEXT[t.kind] || t.kind}</td>
                <td className="muted">{t.note}</td>
                <td className={`num ${pnlClass(t.amount)}`}>{money(t.amount)}</td>
                <td className="num">{money(t.balance_after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
