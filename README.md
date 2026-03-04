# 🎵 Sekra — Emotion-Driven Music Recommendation System

> Type how you feel. Get a Spotify playlist that matches your mood.

Sekra detects the emotional tone of your text using AI, maps it to a curated set of songs, and automatically creates a Spotify playlist in your account — all in one flow.

---

## ✨ How It Works
```
User types: "I feel lonely tonight"
        ↓
  Emotion Detection (Mistral AI)
  → primary: heartbreak, secondary: [sadness, loneliness]
        ↓
  Song Recommendation
  → matches emotion to curated track dataset
        ↓
  Spotify Integration
  → creates playlist + adds tracks to your account
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Emotion Detection | Mistral AI (via API) |
| Music Matching | Preprocessed emotion → song dataset |
| Spotify Integration | Spotify Web API, Spotipy (OAuth only) |
| Frontend | HTML, CSS, JavaScript |

---

## 📁 Project Structure
```
app_1/
├── main.py                        # FastAPI app, endpoints
├── backend/
│   ├── recommend.py               # Emotion detection + song matching
│   └── spotify_playlist.py        # Spotify OAuth + playlist creation
├── frontend/
│   ├── index.html
│   └── (js / css files)
├── .env                           # Spotify credentials (never commit)
└── .spotify_token_cache           # OAuth token cache (never commit)
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourname/sekra.git
cd sekra/app_1
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `app_1/` directory:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

Get these from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

### 5. Configure your Spotify app

In the Spotify Developer Dashboard, set:
- **Redirect URI:** `http://127.0.0.1:8000/callback`
- **APIs used:** Web API, Web Playback SDK
- **User Management:** Add your Spotify account email (required in Development Mode)

> ⚠️ Your Spotify account must have an **active Premium subscription** for the Web API write endpoints to work in Development Mode.

---

## 🚀 Running the App
```bash
uvicorn main:app --reload
```

On first run, Spotify will open a browser window for OAuth authorization. After authorizing, the token is cached in `.spotify_token_cache` for future runs.

Open your browser at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔌 API Endpoints

### `POST /recommend`
Detects emotion from text and returns matching track IDs.

**Request:**
```json
{ "text": "I feel lonely tonight" }
```

**Response:**
```json
{
  "emotion": { "primary": "heartbreak", "secondary": ["sadness", "loneliness"] },
  "spotify_uris": ["4Ttg2ZRg24knfykSp52aiM", "1Y7FQSN29oNXHZBGMkADeH"]
}
```

---

### `POST /create-playlist`
Creates a Spotify playlist and adds the recommended tracks.

**Request:**
```json
{
  "name": "Heartbreak Mood Playlist",
  "spotify_uris": ["4Ttg2ZRg24knfykSp52aiM", "1Y7FQSN29oNXHZBGMkADeH"]
}
```

**Response:**
```json
{
  "playlist_id": "26Lj5ld57gCfF9fg1Qd6pm",
  "playlist_url": "https://open.spotify.com/playlist/26Lj5ld57gCfF9fg1Qd6pm",
  "track_count": 5
}
```

---

## 🔐 OAuth Flow

Sekra uses Spotify's **Authorization Code Flow**:

1. On startup, the app checks for a cached token in `.spotify_token_cache`
2. If none exists, it opens a browser for Spotify login
3. After authorization, Spotify redirects to `http://127.0.0.1:8000/callback`
4. The token is cached locally for future sessions

**Required scopes:**
```
playlist-modify-private
playlist-modify-public
playlist-read-private
```

---

## 🚫 .gitignore

Make sure these are excluded from version control:
```
.env
.spotify_token_cache
.venv/
__pycache__/
```

---

## 📌 Known Limitations

- **Development Mode only** — up to 5 Spotify users can use the app. To allow more users, apply for Extended Access on the Spotify Developer Dashboard.
- **Static emotion-song mapping** — the dataset is preprocessed and not personalized to listening history.
- **Single user session** — the app is designed for one authenticated Spotify account at a time.
- **Spotify API (Feb 2026)** — track insertion uses the `/playlists/{id}/items` endpoint. The older `/tracks` endpoint is no longer supported for Development Mode apps.

---

## 🗺️ Roadmap

- [ ] Replace static dataset with dynamic Spotify search by mood/genre
- [ ] Add user listening history personalization
- [ ] Support multiple concurrent users with per-session OAuth
- [ ] Improve emotion detection with multi-label confidence scores

---

## 📄 License

MIT License — feel free to use, modify, and distribute.