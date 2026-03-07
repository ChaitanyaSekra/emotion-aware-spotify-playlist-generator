document.addEventListener("DOMContentLoaded", () => {
  const submitBtn = document.getElementById("submitBtn");
  const createPlaylistBtn = document.getElementById("createPlaylistBtn");

  const userInput = document.getElementById("userInput");
  const loader = document.getElementById("loader");
  const results = document.getElementById("results");
  const songList = document.getElementById("songList");
  const trackCount = document.getElementById("trackCount");

  const emotionInfo = document.getElementById("emotionInfo");
  const emotionPrimary = document.getElementById("emotionPrimary");
  const emotionSecondary = document.getElementById("emotionSecondary");

  const playlistLink = document.getElementById("playlistLink");
  const spotifyLink = document.getElementById("spotifyLink");

  let currentSongs = [];

  // -------------------------
  // STEP 1: GET RECOMMENDATIONS
  // -------------------------
  submitBtn.addEventListener("click", async () => {
    const text = userInput.value.trim();
    if (!text) {
      userInput.focus();
      return;
    }

    // Reset UI
    loader.classList.remove("hidden");
    results.classList.add("hidden");
    emotionInfo.classList.add("hidden");
    playlistLink.classList.add("hidden");
    createPlaylistBtn.classList.add("hidden");
    songList.innerHTML = "";
    submitBtn.disabled = true;

    try {
      const res = await fetch("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      const data = await res.json();

      loader.classList.add("hidden");
      submitBtn.disabled = false;

      // Emotion chip
      emotionPrimary.textContent = data.emotion.primary;
      const secondaryList = Array.isArray(data.emotion.secondary)
        ? data.emotion.secondary.join(", ")
        : "";
      emotionSecondary.textContent = secondaryList ? `· ${secondaryList}` : "";
      emotionInfo.classList.remove("hidden");

      // Songs
      currentSongs = data.songs;
      trackCount.textContent = `${data.songs.length} tracks`;

      data.songs.forEach((song, i) => {
        const li = document.createElement("li");
        li.className = "song";
        li.innerHTML = `
          <span class="song-index">${String(i + 1).padStart(2, "0")}</span>
          <div class="song-info">
            <span class="song-name">${song.song_name}</span>
            <span class="song-artist">${song.artist_name}</span>
          </div>
          <span class="song-dot"></span>
        `;
        songList.appendChild(li);
      });

      results.classList.remove("hidden");

      if (currentSongs.length > 0) {
        createPlaylistBtn.classList.remove("hidden");
      }

    } catch (err) {
      loader.classList.add("hidden");
      submitBtn.disabled = false;
      console.error(err);
      showError("couldn't get recommendations. try again.");
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
      showError("no spotify tracks available");
      return;
    }

    loader.classList.remove("hidden");
    createPlaylistBtn.disabled = true;
    playlistLink.classList.add("hidden");

    try {
      const emotion = emotionPrimary.textContent || "mood";
      const playlistName = `${capitalize(emotion)} Playlist · Reverie`;

      const res = await fetch("/create-playlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: playlistName,
          spotify_uris: spotifyUris
        })
      });

      const data = await res.json();

      loader.classList.add("hidden");
      createPlaylistBtn.disabled = false;

      spotifyLink.href = data.playlist_url;
      playlistLink.classList.remove("hidden");

    } catch (err) {
      loader.classList.add("hidden");
      createPlaylistBtn.disabled = false;
      console.error(err);
      showError("playlist creation failed. try again.");
    }
  });

  // -------------------------
  // HELPERS
  // -------------------------
  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function showError(msg) {
    const existing = document.querySelector(".error-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "error-toast";
    toast.textContent = msg;
    toast.style.cssText = `
      position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
      background: rgba(255,60,60,0.12); border: 1px solid rgba(255,60,60,0.25);
      color: #ff6b6b; padding: 10px 20px; border-radius: 999px;
      font-size: 0.82rem; font-family: 'DM Sans', sans-serif;
      letter-spacing: 0.04em; z-index: 100;
      animation: fadeUp 0.3s ease both;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }

  // Allow submit with Ctrl+Enter / Cmd+Enter
  userInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      submitBtn.click();
    }
  });
});
