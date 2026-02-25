import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict

# -------------------------
# CONFIG
# -------------------------

SPOTIFY_SCOPE = "playlist-modify-private playlist-modify-public"
REDIRECT_URI = "http://127.0.0.1:8000/callback"

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Spotify credentials not set in environment variables")

# -------------------------
# SPOTIFY CLIENT
# -------------------------

def get_spotify_client() -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SPOTIFY_SCOPE,
            cache_path=".spotify_token_cache"
        )
    )

# -------------------------
# PLAYLIST CREATION
# -------------------------

def create_playlist(
    playlist_name: str,
    spotify_uris: List[str],
    description: str = "Emotion-driven playlist",
    public: bool = False
) -> Dict:
    """
    Creates a Spotify playlist and adds tracks.

    Args:
        playlist_name: Name of the playlist
        spotify_uris: List of Spotify track URIs
        description: Playlist description
        public: Whether playlist is public

    Returns:
        {
            "playlist_id": str,
            "playlist_url": str,
            "track_count": int
        }
    """

    if not spotify_uris:
        raise ValueError("No Spotify URIs provided")

    sp = get_spotify_client()

    user_id = sp.current_user()["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=public,
        description=description
    )

    playlist_id = playlist["id"]

    # Spotify allows max 100 tracks per request
    for i in range(0, len(spotify_uris), 100):
        sp.playlist_add_items(
            playlist_id=playlist_id,
            items=spotify_uris[i:i + 100]
        )

    return {
        "playlist_id": playlist_id,
        "playlist_url": playlist["external_urls"]["spotify"],
        "track_count": len(spotify_uris)
    }