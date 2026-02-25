from typing import Optional
from sqlmodel import SQLModel, Field


# -------------------------
# Artist Table
# -------------------------
class Artist(SQLModel, table=True):
    artist_id: Optional[int] = Field(default=None, primary_key=True)
    name: str


# -------------------------
# Genre Table
# -------------------------
class Genre(SQLModel, table=True):
    genre_id: Optional[int] = Field(default=None, primary_key=True)
    name: str


# -------------------------
# Emotion Table
# -------------------------
class Emotion(SQLModel, table=True):
    emotion_id: Optional[int] = Field(default=None, primary_key=True)
    emotion_name: str = Field(unique=True, index=True)
    description: Optional[str] = None


# -------------------------
# Song Table
# -------------------------
class Song(SQLModel, table=True):
    song_id: Optional[int] = Field(default=None, primary_key=True)

    song_name: str

    # Foreign keys
    artist_id: Optional[int] = Field(default=None, foreign_key="artist.artist_id")
    genre_id: Optional[int] = Field(default=None, foreign_key="genre.genre_id")

    # Emotions (FKs to emotion table)
    p_emotion_id: int = Field(foreign_key="emotion.emotion_id")

    s_emotion_1_id: Optional[int] = Field(default=None, foreign_key="emotion.emotion_id")
    s_emotion_2_id: Optional[int] = Field(default=None, foreign_key="emotion.emotion_id")
    s_emotion_3_id: Optional[int] = Field(default=None, foreign_key="emotion.emotion_id")

    # Metadata
    energy_level: Optional[str] = None
    tempo_category: Optional[str] = None
    language: str = "Hindi"

    # Explicit content flag
    is_explicit: bool = Field(default=False)

    # Spotify
    spotify_uri: Optional[str] = Field(default=None, unique=True)
