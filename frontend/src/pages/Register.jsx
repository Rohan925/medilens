import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, getApiErrorMessage } from "../lib/api";
import "../css/Login.css";

function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const response = await apiFetch("/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(getApiErrorMessage(data, "Registration failed"));
      }

      alert("Account created successfully!");
      navigate("/");

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">

        {/* ✅ disable browser autofill */}
        <form
          className="login-box"
          onSubmit={handleRegister}
          autoComplete="off"
        >
          <h2>Create Account</h2>

          {error && <div className="login-error">{error}</div>}

          <input
            type="email"
            placeholder="Email"
            value={email}
            autoComplete="off"
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            autoComplete="new-password"
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button type="submit">Register</button>

          <p
            style={{
              marginTop: "15px",
              cursor: "pointer",
              color: "#4da6ff",
              textAlign: "center",
            }}
            onClick={() => navigate("/")}
          >
            Already have an account? Login
          </p>

        </form>

      </div>
    </div>
  );
}

export default Register;
