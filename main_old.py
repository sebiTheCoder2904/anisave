import os
import subprocess
from time import sleep
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://aniworld.to/anime/stream"
USERNAME = "midnightlife"
WATCHLIST_URL = f"https://aniworld.to/user/profil/{USERNAME}/watchlist"
DOWNLOAD_DIR = "downloads"
LANGUAGE = "German Dub"

def get_watchlist_slugs():
    r = requests.get(WATCHLIST_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    slugs = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/anime/stream/" in href:
            slug = href.split("/anime/stream/")[1].split("/")[0]
            slugs.add(slug)
    return list(slugs)

def episode_available_by_aniworld(episode_url):
    cmd = [
        "aniworld",
        "-e", episode_url,
        "-a", "download",
        "-L", LANGUAGE,
        "-o", "/tmp"  # dummy output to test availability
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        if "Derzeit keine Streams für diese Episode verfügbar" in output:
            return False
        return True
    except subprocess.SubprocessError:
        return False

def already_downloaded(title):
    path = os.path.join(DOWNLOAD_DIR, title)
    return os.path.isdir(path) and bool(os.listdir(path))

def run_download(episode_url, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Downloading {episode_url} to {output_dir}")
    subprocess.run([
        "aniworld",
        "-e", episode_url,
        "-a", "download",
        "-L", LANGUAGE,
        "-o", output_dir
    ], check=True)

def main():
    slugs = get_watchlist_slugs()
    print(f"Found {len(slugs)} anime in watchlist.")

    for slug in slugs:
        title = slug.replace("-", " ").title()
        if already_downloaded(title):
            print(f"✅ Skipping '{title}' (already downloaded)")
            continue

        print(f"Processing '{title}'")

        season_num = 1
        season_found = False

        while True:
            episode_num = 1
            episode_found = False

            while True:
                episode_url = f"{BASE_URL}/{slug}/staffel-{season_num}/episode-{episode_num}"
                if not episode_available_by_aniworld(episode_url):
                    if episode_num == 1:
                        break  # no episodes in this season, move to next season or finish
                    else:
                        break  # no more episodes in this season

                episode_found = True
                season_found = True
                season_dir = os.path.join(DOWNLOAD_DIR, title, f"Season {season_num}")

                try:
                    run_download(episode_url, season_dir)
                except subprocess.CalledProcessError:
                    print(f"❌ Download failed for {episode_url}")

                episode_num += 1
                sleep(1)  # polite delay between downloads

            if not episode_found:
                break  # no episodes found in this season, stop scanning seasons

            season_num += 1

        if not season_found:
            print(f"⚠️ No episodes found for '{title}'")

if __name__ == "__main__":
    main()
