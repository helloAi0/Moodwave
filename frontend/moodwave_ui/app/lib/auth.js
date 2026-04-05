export function getSpotifyToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("spotify_token");
}

export function setSpotifyToken(token: string) {
  localStorage.setItem("spotify_token", token);
}

export function getAppToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function isFullyAuthenticated() {
  return !!getAppToken() && !!getSpotifyToken();
}