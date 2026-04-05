"use client";

import { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";
import * as Tone from "tone";

export default function MoodWaveUI() {
  const [isConnected, setIsConnected] = useState(false);
  const [audioStarted, setAudioStarted] = useState(false);
  const [engineState, setEngineState] = useState({
    bpm: 60,
    valence: 0,
    energy: 0,
    progress: 0,
  });

  // Keep track of our audio components
  const synthRef = useRef<Tone.FMSynth | null>(null);
  const loopRef = useRef<Tone.Loop | null>(null);

  useEffect(() => {
    // 1. Connect to the FastAPI Docker Backend
    const socket = io("http://localhost:8000", { path: "/ws/socket.io" });

    socket.on("connect", () => setIsConnected(true));
    socket.on("disconnect", () => setIsConnected(false));

    // 2. Listen for the AI Engine's math updates
    socket.on("mood_update", (data) => {
      console.log("Received AI Data:", data);
      
      const newBpm = data.audio_params.bpm;
      const newVolume = data.audio_params.volume;
      
      setEngineState({
        bpm: newBpm,
        valence: data.audio_params.valence_level,
        energy: data.audio_params.energy_level,
        progress: data.progress_pct,
      });

      // 3. Dynamically update the Audio Engine without stopping it
      if (audioStarted && loopRef.current && synthRef.current) {
        Tone.Transport.bpm.rampTo(newBpm, 1); // Smoothly slide to new BPM over 1 second
        synthRef.current.volume.value = Tone.gainToDb(newVolume);
      }
    });

    return () => { socket.disconnect(); };
  }, [audioStarted]);

  const startTherapy = async () => {
    // Browsers require a physical click before they allow audio to play
    await Tone.start();
    
    // Set up a deep, calming FM Synth
    const synth = new Tone.FMSynth({
      harmonicity: 1.5,
      modulationIndex: 3.5,
      oscillator: { type: "sine" },
      modulation: { type: "triangle" }
    }).toDestination();
    
    synthRef.current = synth;

    // Create a loop that plays a note based on the current BPM
    const loop = new Tone.Loop((time) => {
      // The lower the valence (sadder), the lower the note. 
      // Happy = C4, Sad = C2
      const note = engineState.valence > 0 ? "C4" : "C2";
      synth.triggerAttackRelease(note, "8n", time);
    }, "4n");
    
    loopRef.current = loop;

    Tone.Transport.bpm.value = engineState.bpm;
    Tone.Transport.start();
    loop.start(0);
    
    setAudioStarted(true);
  };

  return (
    <div style={{ 
        minHeight: "100vh", 
        display: "flex", 
        flexDirection: "column", 
        alignItems: "center", 
        justifyContent: "center",
        backgroundColor: engineState.valence > 0 ? "#1e3a8a" : "#0f172a", // Blue if happy, Dark if sad
        color: "white",
        transition: "background-color 2s ease"
    }}>
      <h1>🌊 MoodWave Therapy V2</h1>
      <p>Backend Status: {isConnected ? "🟢 Connected" : "🔴 Disconnected"}</p>
      
      {!audioStarted ? (
        <button 
          onClick={startTherapy}
          style={{ padding: "15px 30px", fontSize: "1.2rem", borderRadius: "8px", cursor: "pointer", marginTop: "20px" }}
        >
          Start Audio Engine
        </button>
      ) : (
        <div style={{ marginTop: "40px", textAlign: "center" }}>
          <div style={{ 
              width: "150px", 
              height: "150px", 
              borderRadius: "50%", 
              backgroundColor: "rgba(255,255,255,0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto",
              // CSS animation that beats to the exact BPM coming from the AI
              animation: `pulse ${60 / engineState.bpm}s infinite alternate`
          }}>
             <h2>{engineState.bpm} BPM</h2>
          </div>
          
          <div style={{ marginTop: "30px" }}>
            <p><strong>Iso-Progress:</strong> {engineState.progress}%</p>
            <p><strong>Valence:</strong> {engineState.valence}</p>
            <p><strong>Energy:</strong> {engineState.energy}</p>
          </div>
        </div>
      )}

      {/* Adding the pulse animation via inline style block for simplicity */}
      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          100% { transform: scale(1.1); }
        }
      `}</style>
    </div>
  );
}