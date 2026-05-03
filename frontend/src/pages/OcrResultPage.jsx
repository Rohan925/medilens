import { useLocation } from "react-router-dom";
import ChatBot from "../components/ChatBot";
import logo from "../assets/logo.png";   // ✅ Already present
import "../css/Navbar.css";
import "../css/OcrResultPage.css";

function OcrResultPage() {
  const location = useLocation();
  const state = location.state || {};

  const image = state.image;
  const medicineName = state.medicine || state.name;
  const summary = state.summary;
  const uses = Array.isArray(summary?.uses) ? summary.uses : [];

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
          <h2>{medicineName?.toUpperCase()}</h2>

          {image && (
            <img
              src={image}
              alt="OCR"
              className="ocr-image"
            />
          )}

          <div className="medicine-summary">
            <h3>Summary</h3>

            {summary ? (
              <>
                <p><strong>Category:</strong> {summary.category}</p>
                <p><strong>Uses:</strong> {uses.join(", ")}</p>
                <p>
                  <strong>Prescription:</strong>{" "}
                  {summary.prescription_status || (summary.prescription_required ? "Yes" : "No")}
                </p>
              </>
            ) : (
              <p style={{ opacity: 0.6 }}>
                No summary available.
              </p>
            )}
          </div>
        </div>

        <div className="medicine-chatbot">
          <ChatBot medicineName={medicineName} />
        </div>
      </div>
    </>
  );
}

export default OcrResultPage;