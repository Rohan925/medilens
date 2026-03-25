import { useParams } from "react-router-dom";
import MedicineSummary from "../components/MedicineSummary";
import ChatBot from "../components/ChatBot";
import logo from "../assets/logo.png";   // ✅ Added
import "../css/Navbar.css";
import "../css/MedicinePage.css";

function MedicinePage() {
  const { name } = useParams();

  return (
    <>
      <div className="navbar">
        <div className="navbar-left">
          <img src={logo} alt="Logo" className="navbar-logo" />
          <span>MediLens</span>
        </div>
      </div>

      <div className="medicine-page">
        <div className="medicine-content">
          <h2>{name}</h2>

          <MedicineSummary medicineName={name} />
        </div>

        <div className="medicine-chatbot">
          <ChatBot medicineName={name} />
        </div>
      </div>
    </>
  );
}

export default MedicinePage;