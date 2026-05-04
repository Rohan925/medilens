export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function apiFetch(path, options = {}) {
  return fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
  });
}

export function getApiErrorMessage(data, fallbackMessage) {
  if (!data) {
    return fallbackMessage;
  }

  if (typeof data.detail === "string" && data.detail.trim()) {
    return data.detail;
  }

  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const firstIssue = data.detail[0];
    if (firstIssue && typeof firstIssue.msg === "string" && firstIssue.msg.trim()) {
      return firstIssue.msg;
    }
  }

  return fallbackMessage;
}
