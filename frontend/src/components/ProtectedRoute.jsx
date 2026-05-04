import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { apiFetch } from "../lib/api";

function ProtectedRoute() {
  const [status, setStatus] = useState("loading");
  const location = useLocation();

  useEffect(() => {
    let active = true;

    const verifySession = async () => {
      try {
        const response = await apiFetch("/me");
        if (!active) return;
        setStatus(response.ok ? "authenticated" : "unauthenticated");
      } catch (error) {
        if (!active) return;
        setStatus("unauthenticated");
      }
    };

    verifySession();
    return () => {
      active = false;
    };
  }, []);

  if (status === "loading") {
    return <div style={{ padding: "2rem", textAlign: "center" }}>Checking session...</div>;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
