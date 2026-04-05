"use client";
import { useState } from "react";

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginApp = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      
      if (data.access_token) {
        // Save the app token and route to the dashboard
        localStorage.setItem("token", data.access_token);
        window.location.href = "/dashboard";
      } else { 
        alert("Login failed: Invalid credentials"); 
      }
    } catch (err) { 
      alert("Backend offline? Please ensure Docker is running."); 
    }
  };

  const loginSpotify = () => {
    const CLIENT_ID = "c38ef719fe7b4af3be72edd5784ebecd";
    // 🎯 Note: Make sure http://localhost:3000/callback is registered in your Spotify Dashboard!
    const REDIRECT_URI = "http://localhost:3000/callback";
    const SCOPES = "streaming user-read-email user-read-private user-modify-playback-state";
    const AUTH_ENDPOINT = "https://accounts.spotify.com/authorize";

    // 🎯 DIRECT TOKEN FLOW (Implicit Grant - Bypasses backend)
    window.location.href = 
      `${AUTH_ENDPOINT}?client_id=${CLIENT_ID}` +
      `&response_type=token&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
      `&scope=${encodeURIComponent(SCOPES)}&show_dialog=true`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-10 font-sans">
      <h1 className="text-4xl font-black mb-8 italic">
        MOODWAVE <span className="text-blue-500">RESET</span>
      </h1>
      
      <div className="w-80 flex flex-col gap-4">
        <input 
          className="p-3 rounded-lg text-black outline-none focus:ring-2 focus:ring-blue-500" 
          placeholder="Email" 
          onChange={e => setEmail(e.target.value)} 
        />
        <input 
          className="p-3 rounded-lg text-black outline-none focus:ring-2 focus:ring-blue-500" 
          type="password" 
          placeholder="Password" 
          onChange={e => setPassword(e.target.value)} 
        />
        
        <button 
          className="bg-blue-600 hover:bg-blue-500 transition-colors p-3 rounded-lg font-bold shadow-lg" 
          onClick={loginApp}
        >
          App Login
        </button>
        
        <div className="h-px bg-slate-800 my-4 relative flex items-center justify-center">
          <span className="bg-slate-950 px-3 text-xs text-slate-500 font-bold">OR</span>
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