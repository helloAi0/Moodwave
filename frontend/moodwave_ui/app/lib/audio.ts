import * as Tone from "tone";

let synth: Tone.Synth | null = null;
let therapyOsc: Tone.Oscillator | null = null;

/**
 * Initializes the global Tone.js context.
 * Must be triggered by a user gesture (like a button click).
 */
export async function initAudio() {
  await Tone.start();
  
  if (!synth) {
    // Primary "Heartbeat" Synth
    synth = new Tone.Synth({
      envelope: {
        attack: 0.1,
        release: 1
      }
    }).toDestination();
  }
  
  Tone.Transport.start();
  console.log("🔊 Audio Engine & Transport Initialized");
}

/**
 * Plays the primary rhythmic note (The "Heartbeat").
 * Ramps the global transport BPM to match the AI's pulse.
 */
export function playSound(bpm: number, freq: number) {
  if (!synth) return;
  
  // Set the heart rate of the music
  Tone.Transport.bpm.rampTo(bpm, 0.1);
  
  // Trigger a note at the specific frequency from IsoEngine
  // "8n" is an eighth note duration
  synth.triggerAttackRelease(freq, "8n");
}

/**
 * Manages the background Therapy Layer (Binaural/Isochronic).
 * This creates a constant, subtle tone that shifts frequency based on mood.
 */
export function playTherapyLayer(freq: number) {
  if (!therapyOsc) {
    // Initialize a low-volume pure sine wave for therapy
    therapyOsc = new Tone.Oscillator(freq, "sine").toDestination();
    
    // Keep it subtle (-20dB) so it sits behind the main synth
    therapyOsc.volume.value = -20; 
    therapyOsc.start();
    console.log("🧘 Therapy Layer Started");
  } else {
    // Smoothly transition the background frequency over 1 second
    therapyOsc.frequency.rampTo(freq, 1);
  }
}

/**
 * Optional: Stops all audio if needed (e.g., on Logout)
 */
export function stopAllAudio() {
    if (therapyOsc) {
        therapyOsc.stop();
        therapyOsc = null;
    }
    Tone.Transport.stop();
}