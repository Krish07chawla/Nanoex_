import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "STUDENT" });
  const [error, setError] = useState("");

  if (user) return <Navigate to="/" replace />;

  const change = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="auth-box card stack" onSubmit={submit}>
      <h1>Create account</h1>
      <div>
        <label>Full name</label>
        <input value={form.name} onChange={change("name")} required />
      </div>
      <div>
        <label>Email</label>
        <input type="email" value={form.email} onChange={change("email")} required />
      </div>
      <div>
        <label>Password (at least 6 characters)</label>
        <input type="password" value={form.password} onChange={change("password")} required />
      </div>
      <div>
        <label>I am a</label>
        <select value={form.role} onChange={change("role")}>
          <option value="STUDENT">Student (I want to learn)</option>
          <option value="TRADER">Trader (I want to teach)</option>
        </select>
      </div>
      {error && <div className="message error">{error}</div>}
      <button className="primary full">Sign up</button>
      <div className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </div>
    </form>
  );
}
