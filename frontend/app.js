document.addEventListener("DOMContentLoaded", () => {
  const submitBtn = document.getElementById("submitBtn");
  const createPlaylistBtn = document.getElementById("createPlaylistBtn");

  const userInput = document.getElementById("userInput");
  const loader = document.getElementById("loader");
  const results = document.getElementById("results");
  const songList = document.getElementById("songList");

  const emotionInfo = document.getElementById("emotionInfo");
  const playlistLink = document.getElementById("playlistLink");
  const spotifyLink = document.getElementById("spotifyLink");

  let currentSongs = [];

  // -------------------------
  // STEP 1: GET RECOMMENDATIONS
  // -------------------------
  submitBtn.addEventListener("click", async () => {
    const text = userInput.value.trim();
    if (!text) return;

    loader.classList.remove("hidden");
    results.classList.add("hidden");
    songList.innerHTML = "";
    emotionInfo.classList.add("hidden");
    playlistLink.classList.add("hidden");
    createPlaylistBtn.classList.add("hidden");

    try {
      const res = await fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      const data = await res.json();

      loader.classList.add("hidden");
      results.classList.remove("hidden");

      emotionInfo.textContent = `Detected emotion: ${data.emotion.primary}`;
      emotionInfo.classList.remove("hidden");

      currentSongs = data.songs;

      data.songs.forEach(song => {
        const li = document.createElement("li");
        li.className = "song";
        li.innerHTML = `
          <strong>${song.song_name}</strong><br/>
          <span>${song.artist_name}</span>
        `;
        songList.appendChild(li);
      });

      if (currentSongs.length > 0) {
        createPlaylistBtn.classList.remove("hidden");
      }

    } catch (err) {
      loader.classList.add("hidden");
      alert("Failed to get recommendations");
      console.error(err);
    }
  });

  // -------------------------
  // STEP 2: CREATE PLAYLIST
  // -------------------------
  createPlaylistBtn.addEventListener("click", async () => {
    const spotifyUris = currentSongs
      .map(s => s.spotify_uri)
      .filter(Boolean);

    if (spotifyUris.length === 0) {
      alert("No Spotify URIs available");
      return;
    }

    loader.classList.remove("hidden");
    createPlaylistBtn.disabled = true;

    try {
      const res = await fetch("/create-playlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Emotion Playlist",
          spotify_uris: spotifyUris
        })
      });

      const data = await res.json();

      loader.classList.add("hidden");
      createPlaylistBtn.disabled = false;

      spotifyLink.href = data.playlist_url;
      spotifyLink.textContent = "Open Playlist on Spotify";
      playlistLink.classList.remove("hidden");

    } catch (err) {
      loader.classList.add("hidden");
      createPlaylistBtn.disabled = false;
      alert("Playlist creation failed");
      console.error(err);
    }
  });
});