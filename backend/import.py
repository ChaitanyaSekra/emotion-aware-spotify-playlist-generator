import pandas as pd
from sqlmodel import Session, select
from db import engine
from models import Song, Artist, Genre, Emotion

# -----------------------------
# Helpers
# -----------------------------

def get_or_create_artist(session, artist_name):
    artist = session.exec(
        select(Artist).where(Artist.name == artist_name)
    ).first()
    if not artist:
        artist = Artist(name=artist_name)
        session.add(artist)
        session.commit()
        session.refresh(artist)
    return artist.artist_id


def get_or_create_genre(session, genre_name):
    genre = session.exec(
        select(Genre).where(Genre.name == genre_name)
    ).first()
    if not genre:
        genre = Genre(name=genre_name)
        session.add(genre)
        session.commit()
        session.refresh(genre)
    return genre.genre_id


def get_emotion_id(session, emotion_name):
    if not emotion_name or pd.isna(emotion_name):
        return None
    emotion = session.exec(
        select(Emotion).where(Emotion.emotion_name == emotion_name)
    ).first()
    if not emotion:
        raise ValueError(f"Emotion '{emotion_name}' not found in emotion table")
    return emotion.emotion_id


def parse_explicit(value):
    if isinstance(value, str):
        value = value.strip().lower()
        if value == "explicit":
            return True
        if value == "not_explicit":
            return False
    return False  # safe default

def song_exists(session, spotify_uri):
    if not spotify_uri or pd.isna(spotify_uri):
        return False
    return session.exec(
        select(Song).where(Song.spotify_uri == spotify_uri)
    ).first() is not None



# -----------------------------
# Main Import Function
# -----------------------------


def import_csv(path):
    df = pd.read_csv(path)
    session = Session(engine)

    for idx, row in df.iterrows():
        try:
            # artist & genre
            artist_id = get_or_create_artist(session, row["artist"])
            genre_id = get_or_create_genre(session, row["genre"])

            # emotions
            p_emotion_id = get_emotion_id(session, row["p_emotion"])
            s_emotion_1_id = get_emotion_id(session, row.get("s_emotion_1"))
            s_emotion_2_id = get_emotion_id(session, row.get("s_emotion_2"))
            s_emotion_3_id = get_emotion_id(session, row.get("s_emotion_3"))

            # explicit flag
            is_explicit = parse_explicit(row.get("is_explicit"))

            # skip duplicates
            if song_exists(session, row.get("spotify_uri")):
                print(f"⏭️ Skipping duplicate: {row['song_name']}")
                continue

            song = Song(
                song_name=row["song_name"],
                artist_id=artist_id,
                genre_id=genre_id,
                p_emotion_id=p_emotion_id,
                s_emotion_1_id=s_emotion_1_id,
                s_emotion_2_id=s_emotion_2_id,
                s_emotion_3_id=s_emotion_3_id,
                energy_level=row.get("energy_level"),
                tempo_category=row.get("tempo_category"),
                language=row.get("language", "Hindi") or "Hindi",
                is_explicit=is_explicit,
                spotify_uri=row.get("spotify_uri")
            )

            session.add(song)
            session.commit()


        except Exception as e:
            session.rollback()
            print(f"❌ Error on row {idx + 1}: {e}")

    session.close()
    print("✅ CSV import completed successfully.")


# -----------------------------
# CLI Entry
# -----------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python import_csv_postgres.py path/to/songs.csv")
        exit(1)

    import_csv(sys.argv[1])
