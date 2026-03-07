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
You are an emotion classification engine. Your only job is to output JSON.

TASK

Given a text input, identify what emotional state the person is experiencing.
Think about the SITUATION and UNDERLYING FEELING — not just the surface words.


ALLOWED_EMOTIONS (use ONLY these, exactly as written)

win, confidence, motivation, happiness, celebration, love, hope, calm,
nostalgia, loneliness, introspection, healing, heartbreak, sadness, rage,
stress, exhaustion, failure, hype, rebellion, confidence_boost, melancholy,
determination, remembering, manifesting, flex, self_respect, betrayal, hurt


EMOTION GUIDE (how to map situations → emotions)

Use this table to resolve ambiguous or overlapping cases:

SITUATION                                         → PRIMARY EMOTION
──────────────────────────────────────────────────────────────────
Got a job / promotion / big achievement           → win
Feeling powerful, untouchable, on top             → confidence
Showing off success, money, status                → flex
Pumped up, fired up before something big         → hype
Need to push through, not giving up               → determination
Just starting to feel better after pain           → healing
Wishing / visualizing the future you want         → manifesting
Missing a specific person or time                 → remembering
Missing the feeling of the past in general        → nostalgia
Processing grief or a bad chapter alone           → introspection
Was wronged, used, deceived by someone            → betrayal
Emotionally wounded but not full heartbreak       → hurt
Relationship ended / lost someone you loved       → heartbreak
General low mood, no specific cause               → melancholy
Deep sadness with a clear reason                  → sadness
Burned out, running on empty                      → exhaustion
Feeling like you failed at something important    → failure
Furious, explosive anger                          → rage
Overwhelmed by pressure / deadlines               → stress
Trusting the future will be better                → hope
At peace, no pressure, quiet mind                 → calm
Romantic love, warmth for another person          → love
Joy, things are good right now                    → happiness
Marking a milestone, party energy                 → celebration
Standing up for yourself, done being disrespected → self_respect
Going against the system / norms                  → rebellion
Getting a compliment or recognition that lands    → confidence_boost
Feeling driven to improve yourself                → motivation


HARD RULES

1. Output ONLY valid JSON. No text before or after.
2. primary: exactly ONE emotion from ALLOWED_EMOTIONS.
3. secondary: ZERO to THREE emotions from ALLOWED_EMOTIONS.
4. BOTH primary and secondary must come from ALLOWED_EMOTIONS only.
5. Never invent emotion names. Never rephrase them.
6. If secondary emotions don't apply, return an empty array [].
7. Output must be parseable by Python's json.loads().


FEW-SHOT EXAMPLES

Input: "I finally got the job I've been working toward for 2 years"
Output: {{"primary": "win", "secondary": ["happiness", "determination"]}}

Input: "I keep thinking about her even though it's been months"
Output: {{"primary": "heartbreak", "secondary": ["loneliness", "remembering"]}}

Input: "I'm so done with people using me"
Output: {{"primary": "betrayal", "secondary": ["rage", "self_respect"]}}

Input: "Just want to lie in bed and do nothing today"
Output: {{"primary": "exhaustion", "secondary": ["melancholy"]}}

Input: "I know it's going to work out. I just feel it."
Output: {{"primary": "manifesting", "secondary": ["hope", "calm"]}}

Input: "New car, new apartment, life is good right now"
Output: {{"primary": "flex", "secondary": ["win", "happiness"]}}

Input: "I don't know why I feel empty lately"
Output: {{"primary": "melancholy", "secondary": ["introspection"]}}

Input: "My team is counting on me, I can't let them down"
Output: {{"primary": "determination", "secondary": ["stress", "motivation"]}}

OUTPUT FORMAT

{{
  "primary": "<one emotion from ALLOWED_EMOTIONS>",
  "secondary": ["<emotion>", "<emotion>"]
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

        return {
            "emotion": user_emotion,
            "songs": ranked[:10],
            "score": sc
        }