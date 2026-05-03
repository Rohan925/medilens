import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import ChatBot from "../components/ChatBot";
import OcrCamera from "../components/OcrCamera";
import logo from "../assets/logo.png";   // ✅ Import logo
import "../css/Home.css";
import "../css/Navbar.css";

function Home() {
  const navigate = useNavigate();

  return (
    <>
      <div className="navbar">
        <div className="navbar-left">
          <img src={logo} alt="Logo" className="navbar-logo" />
          <span>MediLens</span>
        </div>
      </div>

      <div className="home-container">
        <SearchBar onSearch={(q) => navigate(`/medicine/${q}`)} />

        <div className="options">
          <ChatBot />
          <OcrCamera />
        </div>
      </div>
    </>
  );
}

export default Home;