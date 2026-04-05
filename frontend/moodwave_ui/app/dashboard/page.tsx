"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import { initAudio, playSound } from "../lib/audio";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getAppToken, getSpotifyToken, clearTokens } from "../lib/auth";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

declare global {
  interface Window {
    onSpotifyWebPlaybackSDKReady: () => void;
    Spotify: {
      Player: new (options: {
        name: string;
        getOAuthToken: (cb: (token: string) => void) => void;
        volume: number;
      }) => {
        addListener: (event: string, cb: (data: { device_id: string }) => void) => void;
        connect: () => void;
      };
    };
  }
}

interface SessionStat {
  bpm: number;
  state: string;
  emotion: string;
  timestamp?: string;
}

interface AudioState {
  bpm: number;
  state: string;
  freq: number;
  progress: number;
}

export default function Dashboard() {
  const [ready, setReady]           = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [deviceId, setDeviceId]     = useState<string | null>(null);
  const [history, setHistory]       = useState<SessionStat[]>([]);
  const [current, setCurrent]       = useState<AudioState>({
    bpm: 80, state: "neutral", freq: 396, progress: 0,
  });

  const socketRef = useRef<Socket | null>(null);

  // ── Token recovery & guard ─────────────────────────────────────────────
  useEffect(() => {
    // Grab Spotify token that may have been placed in the URL by the backend redirect
    const params = new URLSearchParams(window.location.search);
    const urlSpotifyToken = params.get("spotify_token");
    if (urlSpotifyToken) {
      localStorage.setItem("spotify_token", urlSpotifyToken);
      window.history.replaceState({}, "", "/dashboard");
    }

    const appToken     = getAppToken();
    const spotifyToken = getSpotifyToken();

    if (!appToken && !spotifyToken) {
      window.location.href = "/";
      return;
    }

    setReady(true);

    // Fetch initial history
    if (appToken) fetchStats(appToken);
  }, []);

  // ── Spotify Web Playback SDK ───────────────────────────────────────────
  useEffect(() => {
    if (!ready) return;
    const token = getSpotifyToken();
    if (!token) return;

    const script = document.createElement("script");
    script.src   = "https://sdk.scdn.co/spotify-player.js";
    script.async = true;
    document.body.appendChild(script);

    window.onSpotifyWebPlaybackSDKReady = () => {
      const player = new window.Spotify.Player({
        name: "MoodWave Neural Player",
        getOAuthToken: (cb) => cb(token),
        volume: 0.5,
      });
      player.addListener("ready", ({ device_id }) => {
        console.log("✅ Spotify ready, device:", device_id);
        setDeviceId(device_id);
      });
      player.connect();
    };
  }, [ready]);

  // ── Socket.IO + audio ─────────────────────────────────────────────────
  useEffect(() => {
    if (!ready) return;

    const socket = io(API, {
      path: "/ws/socket.io",
      transports: ["websocket"],
    });
    socketRef.current = socket;

    socket.on("audio_update", (incoming: AudioState) => {
      setCurrent({
        bpm:      incoming.bpm   ?? 80,
        state:    incoming.state ?? "neutral",
        freq:     incoming.freq  ?? 396,
        progress: incoming.progress ?? 0,
      });

      if (audioEnabled) {
        playSound(incoming.bpm, incoming.freq);
        const dId = deviceId;
        if (dId) triggerSpotify(incoming.state, dId);
      }

      const token = getAppToken();
      if (token) fetchStats(token);
    });

    return () => { socket.disconnect(); };
  }, [ready, audioEnabled, deviceId]);

  // ── Helpers ───────────────────────────────────────────────────────────
  const fetchStats = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API}/api/sessions/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data: SessionStat[] = await res.json();
        setHistory(data);
      }
    } catch {
      // silently ignore — charts will stay stale
    }
  }, []);

  const triggerSpotify = async (mood: string, dId: string) => {
    const token = getSpotifyToken();
    if (!token) return;

    // Map mood → a representative Spotify track URI
    const tracks: Record<string, string> = {
      calm:    "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
      focus:   "spotify:track:2takcwOaAZWiXQijPHIx7B",
      happy:   "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp",
      neutral: "spotify:track:40v9K651o96AtS2Yp4G64s",
    };
    try {
      await fetch(
        `https://api.spotify.com/v1/me/player/play?device_id=${dId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type":  "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({ uris: [tracks[mood] ?? tracks.neutral] }),
        }
      );
    } catch (err) {
      console.error("Spotify API error:", err);
    }
  };

  const handleLogout = () => {
    clearTokens();
    window.location.href = "/";
  };

  // ── Loading gate ──────────────────────────────────────────────────────
  if (!ready) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-blue-500 font-bold tracking-widest animate-pulse">
        VALIDATING SESSION…
      </div>
    );
  }

  const appToken     = getAppToken();
  const spotifyToken = getSpotifyToken();

  return (
    <div className="min-h-screen bg-[#020617] text-white p-8 font-sans">
      <div className="max-w-5xl mx-auto">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <header className="flex justify-between items-center mb-10">
          <h1 className="text-2xl font-black italic tracking-tighter">
            MOODWAVE <span className="text-blue-500">PRO</span>
          </h1>
          <div className="flex gap-6 items-center">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex flex-col items-end gap-1">
              <span className={appToken ? "text-emerald-500" : "text-red-500"}>
                App: {appToken ? "✅ Authenticated" : "❌ Not logged in"}
              </span>
              <span className={spotifyToken ? "text-emerald-500" : "text-slate-500"}>
                {spotifyToken ? "● Spotify Linked" : "○ No Spotify Token"}
              </span>
              <span className={deviceId ? "text-emerald-500" : "text-slate-500"}>
                {deviceId ? "● Player Ready" : "○ Awaiting Player…"}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-slate-500 underline hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

          {/* ── Live card ──────────────────────────────────────────────── */}
          <div className="bg-slate-900/40 p-10 rounded-[2.5rem] border border-slate-800 flex flex-col items-center backdrop-blur-md shadow-2xl">
            <div
              style={{ animationDuration: `${60 / current.bpm}s` }}
              className={`w-32 h-32 rounded-full border-4 border-blue-600 flex flex-col items-center justify-center mb-4 transition-all
                ${audioEnabled ? "shadow-[0_0_40px_rgba(37,99,235,0.3)] animate-pulse" : ""}`}
            >
              <span className="text-4xl font-black">{current.bpm}</span>
              <span className="text-xs text-slate-400">BPM</span>
            </div>

            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">
              Live State
            </p>
            <h2 className="text-3xl font-bold capitalize mb-2 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
              {current.state}
            </h2>
            <p className="text-xs text-slate-500 mb-8">
              Progress: {Math.round(current.progress * 100)}%
            </p>

            {!audioEnabled ? (
              <button
                onClick={async () => { await initAudio(); setAudioEnabled(true); }}
                className="w-full py-4 bg-blue-600 hover:bg-blue-500 rounded-2xl font-bold transition-all active:scale-95 shadow-lg"
              >
                START SESSION
              </button>
            ) : (
              <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold tracking-widest">
                <span className="h-2 w-2 bg-emerald-400 rounded-full animate-ping" />
                LINK ACTIVE
              </div>
            )}
          </div>

          {/* ── History chart ──────────────────────────────────────────── */}
          <div className="bg-slate-900/40 p-10 rounded-[2.5rem] border border-slate-800 shadow-2xl backdrop-blur-md">
            <h3 className="text-gray-500 text-[10px] font-bold uppercase mb-8 tracking-widest">
              BPM History
            </h3>
            <div className="h-[250px] w-full">
              {history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    {/* XAxis was missing — chart did not render axis labels */}
                    <XAxis
                      dataKey="emotion"
                      tick={{ fill: "#64748b", fontSize: 10 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis hide domain={["dataMin - 5", "dataMax + 5"]} />
                    <Tooltip
                      contentStyle={{
                        background: "#0f172a",
                        border: "1px solid #1e293b",
                        borderRadius: "12px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="bpm"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-700 text-sm font-bold italic animate-pulse">
                  Calibrating Sensors…
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
