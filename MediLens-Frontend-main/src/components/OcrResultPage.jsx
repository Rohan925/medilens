// src/pages/OcrResultPage.jsx
import { useLocation } from "react-router-dom";
import ChatBot from "../components/ChatBot";
import "../css/Navbar.css";
import "../css/OcrResultPage.css";

function OcrResultPage() {
  const location = useLocation();
  const state = location.state || {};

  // Extract values from the backend OCR response
  const image = state.image;
  const medicineName = state.name; // Key fix: correctly mapping 'name' from backend
  const summary = state.summary;
  const citations = state.citations;

  return (
    <>
      <div className="navbar">MediLens</div>

      <div className="medicine-page">
        <div className="medicine-content">
          <h2>{medicineName?.toUpperCase()}</h2>

          {image && (
            <img src={image} alt="OCR" className="ocr-image" />
          )}

          <div className="medicine-summary">
            <h3>Analysis Result</h3>

            {/* Category */}
            <p style={{ marginBottom: "12px" }}>
              <strong>Category:</strong> <span style={{ color: "#fff" }}>{summary?.category || "General"}</span>
            </p>

            {/* Uses (Badges) */}
            {summary?.uses?.length > 0 && (
              <>
                <div className="section-title">Common Uses</div>
                <div className="badges-container">
                  {summary.uses.map((use, i) => (
                    <span key={i} className="pill-badge">{use}</span>
                  ))}
                </div>
              </>
            )}

            {/* Side Effects (List) */}
            {summary?.side_effects?.length > 0 && (
              <>
                <div className="section-title">Potential Side Effects</div>
                <ul className="side-effects-list">
                  {summary.side_effects.map((effect, i) => (
                    <li key={i}>{effect}</li>
                  ))}
                </ul>
              </>
            )}

            {/* Warnings (Box) */}
            {summary?.warnings?.length > 0 && (
              <div className="warning-box">
                {summary.warnings.map((warn, i) => (
                  <span key={i} className="warning-item">
                    <span className="warning-icon">⚠️</span> {warn}
                  </span>
                ))}
              </div>
            )}

            {/* Fallback for legacy/text-only summaries */}
            {!summary?.uses && !summary?.side_effects && summary?.text && (
              <p>{summary.text}</p>
            )}

            {!summary && (
              <p style={{ opacity: 0.6 }}>No summary available for this scan.</p>
            )}

            {citations && citations.length > 0 && (
              <div style={{ marginTop: "1rem" }}>
                <strong>Sources:</strong>
                <ul style={{ listStyle: "none", padding: 0, marginTop: "0.5rem" }}>
                  {citations.map((cite, index) => (
                    <li key={index} style={{ marginBottom: "0.25rem" }}>
                      <a
                        href={cite.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "var(--secondary)", textDecoration: "underline" }}
                      >
                        {cite.source}: {cite.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="medicine-chatbot">
          {/* Ensure the ChatBot is context-aware of the scanned medicine */}
          <ChatBot medicineName={medicineName} />
        </div>
      </div>
    </>
  );
}

export default OcrResultPage;