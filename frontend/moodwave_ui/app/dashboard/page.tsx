"use client";
import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { initAudio, playSound } from "../lib/audio";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// Extend global window for Spotify SDK
declare global {
  interface Window {
    onSpotifyWebPlaybackSDKReady: () => void;
    Spotify: any;
  }
}

export default function Dashboard() {
  const [ready, setReady] = useState(false);
  const [current, setCurrent] = useState({ bpm: 80, state: "neutral", freq: 396 });
  const [history, setHistory] = useState([]);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [deviceId, setDeviceId] = useState<string | null>(null);

  // --- 1. THE GATEKEEPER & TOKEN RECOVERY ---
  useEffect(() => {
    // A. Snatch Spotify token if we just arrived from the redirect
    const params = new URLSearchParams(window.location.search);
    const urlSpotifyToken = params.get("spotify_token");

    if (urlSpotifyToken) {
      localStorage.setItem("spotify_token", urlSpotifyToken);
      // Clean the URL silently without triggering a reload
      window.history.replaceState({}, document.title, "/dashboard");
    }

    // B. Check standard tokens
    const appToken = localStorage.getItem("token"); // Note: Saved as "token" in login.tsx
    const spotifyToken = localStorage.getItem("spotify_token");

    // 🎯 STRICT REQUIREMENT: At least one token must exist
    if (!appToken && !spotifyToken) {
      window.location.href = "/"; // Hard redirect home
    } else {
      setReady(true);
      if (appToken) {
        fetchStats(appToken);
      }
    }
  }, []); // Empty dependency array = Runs exactly once (No loops)

  // --- 2. SPOTIFY SDK (ONLY INITS IF READY) ---
  useEffect(() => {
    if (!ready) return;

    const token = localStorage.getItem("spotify_token");
    if (!token) return;

    const script = document.createElement("script");
    script.src = "https://sdk.scdn.co/spotify-player.js";
    script.async = true;
    document.body.appendChild(script);

    window.onSpotifyWebPlaybackSDKReady = () => {
      const player = new window.Spotify.Player({
        name: "MoodWave Neural Player",
        getOAuthToken: (cb: (token: string) => void) => { cb(token); },
        volume: 0.5
      });

      player.addListener('ready', ({ device_id }: { device_id: string }) => {
        console.log('✅ Spotify Player Ready. Device ID:', device_id);
        setDeviceId(device_id);
      });

      player.connect();
    };
  }, [ready]);

  // --- 3. SOCKETS & NEURAL AUDIO ---
  useEffect(() => {
    if (!ready) return;
    
    const socket = io("http://127.0.0.1:8000", { 
        path: "/ws/socket.io", 
        transports: ["websocket"] 
    });

    socket.on("audio_update", (incoming) => {
      setCurrent({ 
        bpm: incoming.bpm || 80, 
        state: incoming.state || "neutral", 
        freq: incoming.freq || 396 
      });

      if (audioEnabled) {
        playSound(incoming.bpm, incoming.freq);
        if (deviceId) {
            triggerSpotify(incoming.state, deviceId);
        }
      }
      
      const appToken = localStorage.getItem("token");
      if (appToken) fetchStats(appToken);
    });

    return () => { socket.disconnect(); };
  }, [ready, audioEnabled, deviceId]);

  // --- 4. SPOTIFY API TRIGGER ---
  const triggerSpotify = async (mood: string, dId: string) => {
    const token = localStorage.getItem("spotify_token");
    if (!token) return;

    const tracks: Record<string, string> = { 
        calm: "spotify:track:6rqhFgbbKwnb9MLmUQDhG6", 
        focus: "spotify:track:2takcwOaAZWiXQijPHIx7B", 
        happy: "spotify:track:3n3Ppam7vgaVa1iaRUc9Lp",
        neutral: "spotify:track:40v9K651o96AtS2Yp4G64s"
    };
    
    try {
        // 🎯 Fixed template literal syntax for the device ID
        await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${dId}`, {
          method: "PUT",
          body: JSON.stringify({ uris: [tracks[mood] || tracks.neutral] }),
          headers: { 
              "Content-Type": "application/json", 
              "Authorization": `Bearer ${token}` 
          }
        });
    } catch(err) {
        console.error("Spotify API Error:", err);
    }
  };

  const fetchStats = (token: string) => {
    fetch("http://127.0.0.1:8000/api/sessions/stats", { 
        headers: { "Authorization": `Bearer ${token}` } 
    })
      .then(res => res.json())
      .then(setHistory)
      .catch(() => {});
  };

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = "/";
  };

  // --- UI: LOADING STATE ---
  if (!ready) return (
      <div className="min-h-screen bg-black flex items-center justify-center text-blue-500 font-bold tracking-widest animate-pulse">
          VALIDATING NEURAL LINK...
      </div>
  );

  // --- UI: DASHBOARD ---
  return (
    <div className="min-h-screen bg-[#020617] text-white p-8 font-sans">
      <div className="max-w-5xl mx-auto">
        
        {/* HEADER */}
        <header className="flex justify-between items-center mb-10">
          <h1 className="text-2xl font-black italic tracking-tighter">MOODWAVE <span className="text-blue-500">PRO</span></h1>
          <div className="flex gap-6 items-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex flex-col items-end gap-1">
                <span className={localStorage.getItem("token") ? "text-emerald-500" : "text-red-500"}>
                    App Auth: {localStorage.getItem("token") ? "✅ Active" : "❌ Disconnected"}
                </span>
                <span className={deviceId ? "text-emerald-500" : "text-slate-500"}>
                    {deviceId ? "● Spotify Linked" : "○ Waiting for Spotify..."}
                </span>
              </div>
              <button onClick={handleLogout} className="text-xs text-slate-500 underline hover:text-white transition-colors">
                  Logout
              </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* LIVE DATA CARD */}
          <div className="bg-slate-900/40 p-10 rounded-[2.5rem] border border-slate-800 flex flex-col items-center backdrop-blur-md shadow-2xl">
             <div className={`w-32 h-32 rounded-full border-4 border-blue-600 flex items-center justify-center mb-4 transition-all ${audioEnabled ? 'shadow-[0_0_40px_rgba(37,99,235,0.2)] animate-pulse' : ''}`}>
               <span className="text-5xl font-black">{current.bpm}</span>
             </div>
             <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-2">Live Emotion</p>
             <h2 className="text-3xl font-bold capitalize mb-8 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
                 {current.state}
             </h2>
             
             {!audioEnabled ? (
                <button onClick={async () => { await initAudio(); setAudioEnabled(true); }} className="w-full py-4 bg-blue-600 hover:bg-blue-500 rounded-2xl font-bold transition-all active:scale-95 shadow-lg">
                    START SESSION
                </button>
             ) : (
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold tracking-widest">
                    <span className="h-2 w-2 bg-emerald-400 rounded-full animate-ping"></span>
                    LINK ACTIVE
                </div>
             )}
          </div>

          {/* HISTORICAL CHART CARD */}
          <div className="bg-slate-900/40 p-10 rounded-[2.5rem] border border-slate-800 shadow-2xl backdrop-blur-md">
             <h3 className="text-gray-500 text-[10px] font-bold uppercase mb-8 tracking-widest">Biometric History</h3>
             
             {/* 🎯 FIXED HEIGHT CHART GUARD */}
             <div className="h-[250px] w-full min-h-[250px]">
               {history.length > 0 ? (
                 <ResponsiveContainer width="100%" height="100%">
                   <LineChart data={history}>
                      <Line type="monotone" dataKey="bpm" stroke="#3b82f6" strokeWidth={4} dot={false} isAnimationActive={false} />
                      <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
                      <Tooltip contentStyle={{background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px'}} />
                   </LineChart>
                 </ResponsiveContainer>
               ) : (
                 <div className="h-full flex items-center justify-center text-slate-700 text-sm font-bold italic animate-pulse">
                     Calibrating Sensors...
                 </div>
               )}
             </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}