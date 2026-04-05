"use client";

import { useEffect } from "react";

export default function Callback() {
  useEffect(() => {
    const hash = window.location.hash;
    
    // If there is no hash, kick the user back to the login page
    if (!hash) {
      window.location.href = "/";
      return;
    }

    // Extract access_token from the URL hash
    const token = hash.split("&").find(elem => elem.includes("access_token"))?.split("=")[1];

    if (token) {
      localStorage.setItem("spotify_token", token);
      console.log("✅ Spotify Token Saved");
      // 🎯 Route directly to the dashboard upon success
      window.location.href = "/dashboard";
    } else {
      // If the token extraction failed, send them back to login
      window.location.href = "/";
    }
  }, []);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center text-blue-500 font-bold tracking-widest">
      SYNCHRONIZING WITH SPOTIFY...
    </div>
  );
}