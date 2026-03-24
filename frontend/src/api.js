const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

async function readJson(response) {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json();
}

export async function fetchDashboard() {
  const response = await fetch(`${API_BASE}/api/dashboard`);
  return readJson(response);
}

export async function sendChat(payload) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return readJson(response);
}

export async function uploadSubstitutionCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/substitution/preview`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}
