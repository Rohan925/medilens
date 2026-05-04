import { useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import { apiFetch } from "../lib/api";
import "../css/Navbar.css";

function AppNavbar() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await apiFetch("/logout", { method: "POST" });
    } finally {
      navigate("/", { replace: true });
    }
  };

  return (
    <div className="navbar">
      <div className="navbar-left">
        <img src={logo} alt="Logo" className="navbar-logo" />
        <span>MediLens</span>
      </div>

      <div className="navbar-right">
        <button className="navbar-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

export default AppNavbar;
