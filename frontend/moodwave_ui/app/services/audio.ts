import * as Tone from "tone";

// Use a synth that sounds a bit smoother for therapy (FMSynth)
let synth: Tone.FMSynth | null = null;

export async function startAudio() {
  await Tone.start();
  
  if (!synth) {
    synth = new Tone.FMSynth({
      harmonicity: 1.5,
      modulationIndex: 3.5,
      oscillator: { type: "sine" },
      modulation: { type: "triangle" }
    }).toDestination();
  }
  
  console.log("🎧 Audio Engine Ready");
}

export function updateAudio(bpm: number, freq: number) {
  if (!synth) return;

  // Smoothly shift the BPM
  Tone.Transport.bpm.rampTo(bpm, 0.5);
  
  // Play the frequency sent by the IsoEngine
  synth.triggerAttackRelease(freq, "4n");
}