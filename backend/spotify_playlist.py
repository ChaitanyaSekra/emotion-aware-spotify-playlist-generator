import os
from typing import List, Dict
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SPOTIFY_SCOPE = "playlist-modify-private playlist-modify-public playlist-read-private"
REDIRECT_URI = "http://127.0.0.1:8000/callback"

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Spotify credentials not set")

auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path=".spotify_token_cache",
)

sp = spotipy.Spotify(auth_manager=auth_manager)

try:
    print("Checking Spotify authentication...")
    user = sp.me()
    print("Spotify authenticated as:", user["display_name"])
except Exception as e:
    print("Spotify authentication failed:", e)
    raise

token_info = sp.auth_manager.get_cached_token()
print("=== TOKEN DEBUG ===")
print("Scopes:", token_info.get("scope"))
print("Expired:", sp.auth_manager.is_token_expired(token_info))
print("Token (first 20 chars):", token_info.get("access_token", "")[:20])
print("===================")


def create_playlist(
    playlist_name: str,
    spotify_uris: List[str],
    description: str = "Emotion-driven playlist",
    public: bool = False
) -> Dict:

    spotify_uris = [
        uri if uri.startswith("spotify:track:") else f"spotify:track:{uri}"
        for uri in spotify_uris
        if uri
    ]

    if not spotify_uris:
        raise ValueError("No valid Spotify tracks provided")

    playlist = sp._post(
        "me/playlists",
        payload={"name": playlist_name, "description": description, "public": True}
    )

    playlist_id = playlist["id"]
    print("Playlist created:", playlist_id)

    # ✅ Use cached token — same one that just created the playlist
    token_info = sp.auth_manager.get_cached_token()
    token = token_info["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for i in range(0, len(spotify_uris), 100):
        batch = spotify_uris[i:i + 100]

        # ✅ Debug is now INSIDE the loop, after headers and batch exist
        print("=== REQUEST DEBUG ===")
        print("URL:", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks")
        print("Headers:", headers)
        print("Payload:", {"uris": batch})
        print("====================")

        res = requests.post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
            headers=headers,
            json={"uris": batch}
        )
        if res.status_code not in (200, 201):
            print(f"[ERROR] Adding tracks failed: {res.status_code} - {res.text}")
            res.raise_for_status()
        print(f"Batch {i//100 + 1} added. snapshot_id: {res.json().get('snapshot_id')}")

    return {
        "playlist_id": playlist_id,
        "playlist_url": playlist["external_urls"]["spotify"],
        "track_count": len(spotify_uris),
    }