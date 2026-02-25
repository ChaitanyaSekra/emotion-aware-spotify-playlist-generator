from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List

# Backend logic
from backend.recommend import get_recommendations
from backend.spotify_playlist import create_playlist

app = FastAPI(title="Emotion Music API")

# -------------------------
# FRONTEND SERVING
# -------------------------

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# Spotify OAuth callback (UX only)
@app.get("/callback", response_class=HTMLResponse)
def spotify_callback():
    return """
    <html>
        <head>
            <title>Spotify Authorized</title>
            <style>
                body {
                    background: #121212;
                    color: #1db954;
                    font-family: system-ui, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
            </style>
        </head>
        <body>
            <h2>Spotify authorization successful. You can close this tab.</h2>
        </body>
    </html>
    """

# -------------------------
# MIDDLEWARE
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# REQUEST MODELS
# -------------------------

class EmotionRequest(BaseModel):
    text: str

class PlaylistRequest(BaseModel):
    name: str
    spotify_uris: List[str]

# -------------------------
# API ENDPOINTS
# -------------------------

# FAST: emotion → songs (NO Spotify here)
@app.post("/recommend")
def recommend(req: EmotionRequest):
    return get_recommendations(req.text)

# SLOW: Spotify playlist creation ONLY
@app.post("/create-playlist")
def create_playlist_endpoint(req: PlaylistRequest):
    return create_playlist(
        playlist_name=req.name,
        spotify_uris=req.spotify_uris,
        public=False
    )