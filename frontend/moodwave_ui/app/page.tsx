"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const SPOTIFY_CLIENT_ID = process.env.NEXT_PUBLIC_SPOTIFY_CLIENT_ID ?? "";
const SPOTIFY_REDIRECT_URI =
  process.env.NEXT_PUBLIC_SPOTIFY_REDIRECT_URI ?? "http://localhost:3000/callback";

type Tab = "login" | "register";

export default function Home() {
  const [tab, setTab]         = useState<Tab>("login");
  const [email, setEmail]     = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);

  // ── App auth ────────────────────────────────────────────────────────────
  const handleAppAuth = async () => {
    setError("");
    if (!email || !password) {
      setError("Please enter email and password.");
      return;
    }
    setLoading(true);
    try {
      const endpoint = tab === "login" ? "/api/auth/login" : "/api/auth/register";
      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail ?? "Authentication failed.");
        return;
      }

      localStorage.setItem("token", data.access_token);
      window.location.href = "/dashboard";
    } catch {
      setError("Backend offline. Make sure Docker is running.");
    } finally {
      setLoading(false);
    }
  };

  // ── Spotify implicit grant ───────────────────────────────────────────────
  const loginSpotify = () => {
    if (!SPOTIFY_CLIENT_ID) {
      setError("NEXT_PUBLIC_SPOTIFY_CLIENT_ID is not set in .env.local");
      return;
    }
    const SCOPES =
      "streaming user-read-email user-read-private user-modify-playback-state";
    window.location.href =
      `https://accounts.spotify.com/authorize` +
      `?client_id=${SPOTIFY_CLIENT_ID}` +
      `&response_type=token` +
      `&redirect_uri=${encodeURIComponent(SPOTIFY_REDIRECT_URI)}` +
      `&scope=${encodeURIComponent(SCOPES)}` +
      `&show_dialog=true`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-10 font-sans">
      <h1 className="text-4xl font-black mb-2 italic">
        MOOD<span className="text-blue-500">WAVE</span>
      </h1>
      <p className="text-slate-500 text-sm mb-8">Emotion-driven music therapy</p>

      {/* Tab switcher */}
      <div className="flex mb-6 bg-slate-800 rounded-lg p-1 gap-1">
        {(["login", "register"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setError(""); }}
            className={`px-6 py-2 rounded-md text-sm font-bold transition-colors capitalize
              ${tab === t ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"}`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="w-80 flex flex-col gap-4">
        {error && (
          <div className="bg-red-900/40 border border-red-500 text-red-300 text-sm px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        <input
          className="p-3 rounded-lg bg-slate-800 text-white outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAppAuth()}
        />
        <input
          className="p-3 rounded-lg bg-slate-800 text-white outline-none focus:ring-2 focus:ring-blue-500"
          type="password"
          placeholder={tab === "register" ? "Password (min 8 chars)" : "Password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAppAuth()}
        />

        <button
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-colors p-3 rounded-lg font-bold shadow-lg capitalize"
          onClick={handleAppAuth}
          disabled={loading}
        >
          {loading ? "Please wait…" : tab === "login" ? "Login" : "Create Account"}
        </button>

        <div className="relative flex items-center my-2">
          <div className="flex-1 h-px bg-slate-700" />
          <span className="mx-3 text-xs text-slate-500 font-bold">OR</span>
          <div className="flex-1 h-px bg-slate-700" />
        </div>

        <button
          className="bg-[#1DB954] hover:bg-[#1ed760] transition-colors p-3 rounded-lg font-bold text-black shadow-lg"
          onClick={loginSpotify}
        >
          Connect Spotify 🎧
        </button>
      </div>
    </div>
  );
}
