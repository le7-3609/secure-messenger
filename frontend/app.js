// app.js — transport layer + toast system
// Used by both index.html and chat.html

const API = "";  // same origin — FastAPI serves both the UI and the API

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

async function apiRegister(username, password) {
  const r = await fetch(`${API}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (r.status === 201) return true;
  const err = await r.json();
  const detail = err.detail;
  const msg = Array.isArray(detail)
    ? detail.map(e => e.msg).join("; ")
    : (detail ?? "Registration failed");
  showToast(msg, "error");
  return false;
}

async function apiLogin(username, password) {
  const r = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (r.status === 200) return (await r.json()).access_token;
  const err = await r.json();
  const detail = err.detail;
  const msg = Array.isArray(detail)
    ? detail.map(e => e.msg).join("; ")
    : (detail ?? "Login failed");
  showToast(msg, "error");
  return null;
}

// ---------------------------------------------------------------------------
// Messages
// ---------------------------------------------------------------------------

async function apiGetMessages(token) {
  const r = await fetch(`${API}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (r.ok) return r.json();
  showToast("Could not load messages", "error");
  return [];
}

async function apiSend(token, recipients, content) {
  const r = await fetch(`${API}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ recipients, content }),
  });
  if (r.status === 201) return true;
  const err = await r.json();
  showToast(err.detail ?? "Failed to send message", "error");
  return false;
}

// ---------------------------------------------------------------------------
// SSE stream
// ---------------------------------------------------------------------------

function openStream(token, onMessage) {
  const es = new EventSource(`${API}/stream?token=${encodeURIComponent(token)}`);
  es.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      onMessage(msg.sender, msg.content);
    } catch (_) {}
  };
  es.onerror = () => showToast("Stream disconnected", "error");
}

// ---------------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------------

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}
