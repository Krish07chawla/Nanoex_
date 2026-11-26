// All the pages and who may open them.

import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { useLive } from "./live";
import Navbar from "./components/Navbar";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Market from "./pages/Market";
import Portfolio from "./pages/Portfolio";
import Orders from "./pages/Orders";
import Wallet from "./pages/Wallet";
import Advisor from "./pages/Advisor";
import Classes from "./pages/Classes";
import ClassRoom from "./pages/ClassRoom";
import Replay from "./pages/Replay";
import Leaderboard from "./pages/Leaderboard";
import Users from "./pages/admin/Users";
import UserDetail from "./pages/admin/UserDetail";
import Audit from "./pages/admin/Audit";

const HOME = { STUDENT: "/dashboard", TRADER: "/classes", ADMIN: "/admin/users" };

// Only let in people who are logged in (and have the right role)
function Protected({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page">Loading...</div>;
  return <Navigate to={user ? HOME[user.role] : "/login"} replace />;
}

function Toasts() {
  const { notices } = useLive();
  return (
    <div className="toasts">
      {notices.map((n) => (
        <div className="toast" key={n.id}>
          {n.text}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const { user } = useAuth();
  const student = ["STUDENT"];

  return (
    <>
      {user && <Navbar />}
      {user && <Toasts />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/dashboard" element={<Protected roles={student}><Dashboard /></Protected>} />
        <Route path="/portfolio" element={<Protected roles={student}><Portfolio /></Protected>} />
        <Route path="/orders" element={<Protected roles={student}><Orders /></Protected>} />
        <Route path="/wallet" element={<Protected roles={student}><Wallet /></Protected>} />
        <Route path="/advisor" element={<Protected roles={student}><Advisor /></Protected>} />

        <Route path="/market" element={<Protected><Market /></Protected>} />
        <Route path="/classes" element={<Protected><Classes /></Protected>} />
        <Route path="/classes/:id" element={<Protected><ClassRoom /></Protected>} />
        <Route path="/classes/:id/replay" element={<Protected><Replay /></Protected>} />
        <Route path="/leaderboard" element={<Protected><Leaderboard /></Protected>} />

        <Route path="/admin/users" element={<Protected roles={["ADMIN"]}><Users /></Protected>} />
        <Route path="/admin/users/:id" element={<Protected roles={["ADMIN"]}><UserDetail /></Protected>} />
        <Route path="/admin/audit" element={<Protected roles={["ADMIN"]}><Audit /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
