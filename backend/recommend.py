from typing import List, Dict
from sqlmodel import select
from backend.db import get_session
from backend.models import Song, Emotion, Artist
import subprocess
import json

# ---- EMOTIONS ----
EMOTIONS = {
    "win", "confidence", "motivation", "happiness", "celebration",
    "love", "hope", "calm", "nostalgia", "loneliness",
    "introspection", "healing", "heartbreak", "sadness",
    "rage", "stress", "exhaustion", "failure", "hype",
    "rebellion", "confidence_boost", "melancholy",
    "determination", "remembering", "manifesting",
    "flex", "self_respect", "betrayal", "hurt"
}

PRIMARY_SCORE = 100
SECONDARY_SCORE = 30
CLUSTER_SCORE = 15

EMOTION_CLUSTERS = {
    # ───────────────
    # PAIN CORE
    # ───────────────
    "hurt": [
        "sadness",
        "heartbreak",
        "betrayal",
        "loneliness"
    ],

    "sadness": [
        "melancholy",
        "loneliness",
        "hurt"
    ],

    "heartbreak": [
        "hurt",
        "sadness",
        "nostalgia"
    ],

    "betrayal": [
        "hurt",
        "rage"
    ],

    # ───────────────
    # INTROSPECTION / LOW ENERGY
    # ───────────────
    "melancholy": [
        "sadness",
        "nostalgia",
        "introspection"
    ],

    "nostalgia": [
        "remembering",
        "melancholy"
    ],

    "loneliness": [
        "sadness",
        "introspection",
        "hurt"
    ],

    "introspection": [
        "loneliness",
        "melancholy",
        "healing"
    ],

    # ───────────────
    # RECOVERY
    # ───────────────
    "healing": [
        "hope",
        "calm",
        "introspection"
    ],

    "hope": [
        "healing",
        "motivation"
    ],

    "calm": [
        "healing",
        "introspection"
    ],

    # ───────────────
    # ENERGY / DRIVE
    # ───────────────
    "confidence": [
        "confidence_boost",
        "self_respect",
        "flex"
    ],

    "confidence_boost": [
        "confidence",
        "motivation"
    ],

    "motivation": [
        "determination",
        "hype"
    ],

    "determination": [
        "motivation",
        "confidence"
    ],

    "hype": [
        "motivation",
        "confidence"
    ],

    # ───────────────
    # AGGRESSION / RELEASE
    # ───────────────
    "rage": [
        "betrayal",
        "rebellion"
    ],

    "rebellion": [
        "rage",
        "self_respect"
    ],

    # ───────────────
    # MEMORY / MEANING
    # ───────────────
    "remembering": [
        "nostalgia",
        "melancholy"
    ]
}

# ---------------- LLM ----------------

def extract_emotions(text: str) -> Dict:
    prompt = f"""
You are a classification engine, not a conversational assistant.

TASK:
Classify the emotional intent of the given text. You need to get the emotions correct of what the user could be feeling.
for example: I got a job will mean they won in life so "win","confidence","flex","happiness" these kind of emotions are what the user would be feeling

emotions like dreaming will equivilate to manifesting
wishing for something will count in manifesting

RULES (MANDATORY):
1. You MUST output valid JSON only.
2. Do NOT include explanations, comments, or extra text.
3. Select EXACTLY ONE primary emotion.
4. Select ZERO TO THREE secondary emotions.
5. ALL emotions MUST be chosen ONLY from the ALLOWED_EMOTIONS list.
6. If no secondary emotions apply, return an empty array.
7. If you are uncertain, choose the closest matching emotion FROM THE LIST.
8. NEVER invent new emotions.
9. NEVER rephrase emotion names.
10. Output MUST be parseable by json.loads().

ALLOWED_EMOTIONS:
[
  "win",
  "confidence",
  "motivation",
  "happiness",
  "celebration",
  "love",
  "hope",
  "calm",
  "nostalgia",
  "loneliness",
  "introspection",
  "healing",
  "heartbreak",
  "sadness",
  "rage",
  "stress",
  "exhaustion",
  "failure",
  "hype",
  "rebellion",
  "confidence_boost",
  "melancholy",
  "determination",
  "remembering",
  "manifesting",
  "flex",
  "self_respect",
  "betrayal",
  "hurt"
]

PRIMARY EMOTION SELECTION RULE:
Choose the emotion that best explains the SITUATION described, not surface feelings or keywords.

OUTPUT FORMAT (STRICT):
{{
  "primary": "<one emotion from ALLOWED_EMOTIONS>",
  "secondary": ["<emotion>", "<emotion>", "<emotion>"]
}}

TEXT:
{text}
"""

    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )

    raw_output = result.stdout.decode().strip()

    # 🔍 CRITICAL DEBUG PRINT
    print("\n===== RAW MISTRAL OUTPUT =====")
    print(raw_output)
    print("===== END RAW OUTPUT =====\n")

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError("Mistral returned invalid JSON")

    # 🔍 PRINT PARSED DATA BEFORE VALIDATION
    print("Parsed emotion object:", data)

    # NOW validate
    primary = data.get("primary")
    secondary = data.get("secondary", [])

    if primary not in EMOTIONS:
        raise ValueError(f"Invalid primary emotion from Mistral: {primary}")

    secondary = [
        e for e in secondary
        if e in EMOTIONS and e != primary
    ][:3]

    return {
        "primary": primary,
        "secondary": secondary
    }

    #return data

# ---------------- SCORING ----------------

def score_song(song, user, id_to_emotion):
    score = 0

    song_primary = id_to_emotion[song.p_emotion_id]
    song_secondaries = [
        id_to_emotion[e] for e in
        [song.s_emotion_1_id, song.s_emotion_2_id, song.s_emotion_3_id]
        if e
    ]

    if song_primary == user["primary"]:
        score += PRIMARY_SCORE
    elif song_primary in EMOTION_CLUSTERS.get(user["primary"], []):
        score += CLUSTER_SCORE

    for ue in user["secondary"]:
        if ue in song_secondaries:
            score += SECONDARY_SCORE
        elif any(
            ue in EMOTION_CLUSTERS.get(se, [])
            for se in song_secondaries
        ):
            score += CLUSTER_SCORE

    if song_secondaries:
        score = int(score * (1 / len(song_secondaries) + 0.5))

    return score

# ---------------- MAIN ENTRY ----------------

def get_recommendations(text: str) -> Dict:
    user_emotion = extract_emotions(text)
    print("\n--- MISTRAL EMOTION OUTPUT ---")
    print(f"Primary   : {user_emotion['primary']}")
    print(f"Secondary : {user_emotion['secondary']}")
    print("------------------------------\n")

    with get_session() as session:
        emotions = session.exec(select(Emotion)).all()
        name_to_id = {e.emotion_name: e.emotion_id for e in emotions}
        id_to_name = {v: k for k, v in name_to_id.items()}

        emotion_ids = [name_to_id[user_emotion["primary"]]] + [
            name_to_id[e] for e in user_emotion["secondary"]
        ]

        songs = session.exec(
            select(Song, Artist)
            .join(Artist, Song.artist_id == Artist.artist_id)
            .where(
                (Song.p_emotion_id.in_(emotion_ids)) |
                (Song.s_emotion_1_id.in_(emotion_ids)) |
                (Song.s_emotion_2_id.in_(emotion_ids)) |
                (Song.s_emotion_3_id.in_(emotion_ids))
            )
        ).all()

        ranked = []
        for song, artist in songs:
            sc = score_song(song, user_emotion, id_to_name)
            if sc > 0:
                ranked.append({
                    "song_name": song.song_name,
                    "artist_name": artist.name,
                    "spotify_uri": song.spotify_uri,
                    "score": sc
                })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        print(ranked)
        print("STEP 3: Creating Spotify playlist")
        
        from backend.spotify_playlist import create_playlist

        spotify_uris = [
            s["spotify_uri"]
            for s in ranked
            if s["spotify_uri"]
        ]
        playlist = create_playlist(
            playlist_name=f"Feeling: {user_emotion['primary']}",
            spotify_uris=spotify_uris,
            description=f"Generated from emotion: {user_emotion}",
            public=False
        )

        print("STEP 4: Spotify playlist created")

        return {
        "emotion": user_emotion,
        "songs": ranked[:5],
        }