// Top menu. The links depend on the role of the logged-in user.

import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { useLive } from "../live";

const LINKS = {
  STUDENT: [
    ["/dashboard", "Dashboard"],
    ["/market", "Market"],
    ["/portfolio", "Portfolio"],
    ["/orders", "Orders"],
    ["/wallet", "Wallet"],
    ["/advisor", "AI Advisor"],
    ["/classes", "Classes"],
    ["/leaderboard", "Leaderboard"],
  ],
  TRADER: [
    ["/classes", "My Classes"],
    ["/market", "Market"],
  ],
  ADMIN: [
    ["/admin/users", "Users"],
    ["/admin/audit", "Audit log"],
    ["/market", "Market"],
    ["/leaderboard", "Leaderboard"],
  ],
};

function FeedBar() {
  const { info } = useLive();
  let source = "Connecting to the price feed...";
  if (info.source === "yahoo") source = "Prices: Yahoo Finance (NSE), delayed about 15 minutes";
  if (info.source === "demo") source = "Prices: DEMO feed (simulated, not real prices)";
  const market = info.market_open === undefined ? "" : info.market_open ? "Market is open" : "Market is closed";
  return (
    <div className="feed-bar">
      <div>
        {source} {market && "· " + market} · Virtual money only, not financial advice.
      </div>
    </div>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function signOut() {
    logout();
    navigate("/login");
  }

  return (
    <>
      <div className="navbar">
        <div className="navbar-inner">
          <span className="brand">
            Nano<span>EX</span>
          </span>
          <nav className="nav-links">
            {LINKS[user.role].map(([path, label]) => (
              <NavLink key={path} to={path} className={({ isActive }) => (isActive ? "active" : "")}>
                {label}
              </NavLink>
            ))}
          </nav>
          <span className="muted">
            {user.name} <span className="badge">{user.role}</span>
          </span>
          <button className="small" onClick={signOut}>
            Log out
          </button>
        </div>
      </div>
      <FeedBar />
    </>
  );
}
