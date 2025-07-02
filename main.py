import requests
from bs4 import BeautifulSoup
import subprocess
import os

USER = "yourUser"
WATCHLIST_URL = f"https://aniworld.to/user/profil/{USER}/watchlist"
BASE_URL = "https://aniworld.to/anime/stream"
LANGUAGE = "German Dub"
DOWNLOADS_DIR = "downloads"

def get_anime_slugs_from_watchlist(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    slugs = set()
    for a in soup.select("a[href*='/anime/stream/']"):
        href = a['href']
        parts = href.split('/')
        if len(parts) >= 4:
            slugs.add(parts[3])  # the slug right after /anime/stream/
    return list(slugs)

def episode_available_by_aniworld(episode_url):
    cmd = [
        "aniworld",
        "-e", episode_url,
        "-a", "download",
        "-L", LANGUAGE,
        "-o", "/tmp"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        if "Derzeit keine Streams für diese Episode verfügbar" in output:
            return False
        return True
    except subprocess.TimeoutExpired:
        # Assume episode exists if timeout (partial download aborted)
        return True
    except subprocess.SubprocessError:
        return False

def download_episode(anime_slug, season_num, episode_num):
    episode_url = f"{BASE_URL}/{anime_slug}/staffel-{season_num}/episode-{episode_num}"
    output_path = os.path.join(DOWNLOADS_DIR, anime_slug.replace("-", " ").title(), f"Season {season_num}")
    os.makedirs(output_path, exist_ok=True)
    cmd = [
        "aniworld",
        "-e", episode_url,
        "-a", "download",
        "-L", LANGUAGE,
        "-o", output_path
    ]
    print(f"Downloading: {episode_url}")
    subprocess.run(cmd)

def download_anime(anime_slug):
    print(f"Starting download for: {anime_slug}")
    season_num = 1
    while True:
        season_folder = os.path.join(DOWNLOADS_DIR, anime_slug.replace("-", " ").title(), f"Season {season_num}")
        # If whole season folder exists and has files, skip season
        if os.path.exists(season_folder) and os.listdir(season_folder):
            season_num += 1
            continue

        episode_num = 1
        any_episode_found = False
        while True:
            episode_url = f"{BASE_URL}/{anime_slug}/staffel-{season_num}/episode-{episode_num}"
            print(f"Checking episode: {episode_url}")
            if not episode_available_by_aniworld(episode_url):
                break
            any_episode_found = True
            download_episode(anime_slug, season_num, episode_num)
            episode_num += 1

        if not any_episode_found:
            break  # no episodes found in this season -> stop
        season_num += 1

def main():
    anime_slugs = get_anime_slugs_from_watchlist(WATCHLIST_URL)
    print(f"Found {len(anime_slugs)} anime in watchlist.")
    for slug in anime_slugs:
        download_anime(slug)
    print("All downloads complete.")

if __name__ == "__main__":
    main()
