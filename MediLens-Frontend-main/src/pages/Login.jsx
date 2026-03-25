import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../css/Login.css";
import logo from "../assets/logo.png";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      // save logged-in user
      localStorage.setItem("user", data.email);

      // redirect
      navigate("/home");

    } catch (err) {
      setError("Invalid email or password");
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">

        <img src={logo} alt="MediLens Logo" className="login-logo" />

        {/* ✅ autofill disabled */}
        <form
          className="login-box"
          onSubmit={handleLogin}
          autoComplete="off"
        >
          <h2>MediLens Login</h2>

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

          <button type="submit">Login</button>

          {/* Register link */}
          <p
            style={{
              marginTop: "15px",
              cursor: "pointer",
              color: "#4da6ff",
              textAlign: "center"
            }}
            onClick={() => navigate("/register")}
          >
            New user? Register here
          </p>

        </form>

      </div>
    </div>
  );
}

export default Login;