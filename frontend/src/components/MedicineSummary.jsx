import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function MedicineSummary({ medicineName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!medicineName) return;

    const fetchSummary = async () => {
      setLoading(true);
      setError("");

      try {
        const res = await apiFetch("/search", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: medicineName,
          }),
        });

        if (!res.ok) {
          throw new Error("Search request failed");
        }

        const data = await res.json();
        setData(data);
      } catch (err) {
        setError("Failed to load summary.");
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [medicineName]);

  return (
    <div className="medicine-summary">
      {loading && <p>Loading summary...</p>}

      {!loading && data && (
        <div style={{ textAlign: "left" }}>
          {/* Header Removed (Handled by MedicinePage) */}

          <p style={{ color: "#888", marginBottom: "1rem" }}>
            <strong>Category:</strong> {data.category}
          </p>

          {/* Uses */}
          {data.uses && data.uses.length > 0 && (
            <div className="summary-section" style={{ marginBottom: "1rem" }}>
              <h3>Uses</h3>
              <ul style={{ paddingLeft: "1.2rem", marginTop: "0.5rem" }}>
                {data.uses.map((u, i) => <li key={i}>{u}</li>)}
              </ul>
            </div>
          )}

          {/* Mechanism */}
          {data.mechanism && data.mechanism.length > 0 && (
            <div className="summary-section" style={{ marginBottom: "1rem" }}>
              <h3>Mechanism of Action</h3>
              <ul style={{ paddingLeft: "1.2rem", marginTop: "0.5rem" }}>
                {data.mechanism.map((m, i) => <li key={i}>{m}</li>)}
              </ul>
            </div>
          )}

          {/* Prescription Status */}
          <div style={{ marginBottom: "1rem" }}>
            <strong>Prescription Status: </strong>
            <span style={{
              padding: "2px 8px",
              borderRadius: "4px",
              backgroundColor: data.prescription_status?.includes("OTC") ? "#e6f4ea" : "#fce8e6",
              color: data.prescription_status?.includes("OTC") ? "#1e8e3e" : "#c5221f",
              fontWeight: "bold"
            }}>
              {data.prescription_status || data.prescription_required}
            </span>
          </div>



          {/* Citations */}
          {data.citations && data.citations.length > 0 && (
            <div style={{ marginTop: "2rem", fontSize: "0.9rem", borderTop: "1px solid #eee", paddingTop: "1rem" }}>
              <strong>Citations:</strong>
              <ul style={{ listStyle: "none", padding: 0, marginTop: "0.5rem" }}>
                {data.citations.map((cite, index) => (
                  <li key={index} style={{ marginBottom: "0.25rem" }}>
                    <span style={{ marginRight: "0.5rem", color: "#666" }}>[{index + 1}]</span>
                    {cite.url ? (
                      <a
                        href={cite.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "#1a73e8", textDecoration: "none" }}
                      >
                        {cite.source}
                      </a>
                    ) : (
                      <span style={{ color: "#333" }}>{cite.source}</span>
                    )}

                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!loading && !data && (
        <p style={{ opacity: 0.6 }}>No summary available.</p>
      )}

      {error && (
        <p style={{ color: "#c5221f", marginTop: "0.75rem" }}>{error}</p>
      )}
    </div>
  );
}
