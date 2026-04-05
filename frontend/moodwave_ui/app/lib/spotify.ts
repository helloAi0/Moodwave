export async function playTrack(uri: string) {
  const token = localStorage.getItem("spotify_token");
  if (!token) return;

  try {
    await fetch("https://api.spotify.com/v1/me/player/play", {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ uris: [uri] })
    });
  } catch (err) {
    console.error("Spotify Play Error:", err);
  }
}