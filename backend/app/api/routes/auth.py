import base64
import httpx
import os
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse

# --- CONFIG (Hardcoded for testing - move to .env later) ---
CLIENT_ID = "c38ef719fe7b4af3be72edd5784ebecd"
CLIENT_SECRET = "aa207248e129489bad731bed057dab0b"
REDIRECT_URI = "http://127.0.0.1:8000/api/auth/callback"
FRONTEND_DASHBOARD = "http://localhost:3000/dashboard"

router = APIRouter()

@router.get("/callback")
async def spotify_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    🎯 THE REDIRECT FIX:
    This route receives the code from Spotify, exchanges it for a token,
    and sends it to the frontend dashboard exactly ONCE.
    """
    
    # 1. Handle user cancellation or Spotify errors
    if error or not code:
        print(f"⚠️ Spotify Auth Failed: {error}")
        return RedirectResponse(url=f"http://localhost:3000/?error=spotify_denied")

    # 2. Prepare the Basic Auth Header
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()

    async with httpx.AsyncClient() as client:
        # 3. Exchange code for Access Token
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
    
    token_data = response.json()
    
    # Check if the exchange actually worked
    if "error" in token_data:
        print(f"❌ Token Exchange Error: {token_data}")
        return RedirectResponse(url=f"http://localhost:3000/?error=token_failed")

    access_token = token_data.get("access_token")
    
    # ✅ SUCCESS: Redirect to dashboard with the token in the query params.
    # The Frontend Dashboard will grab this and save it to localStorage.
    return RedirectResponse(url=f"{FRONTEND_DASHBOARD}?spotify_token={access_token}")