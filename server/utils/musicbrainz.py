"""MusicBrainz integration for fetching album artwork."""
import re
import time
import random
import requests
from config import MUSICBRAINZ_CACHE_SIZE_LIMIT
from utils.image_utils import resize_image

musicbrainz_cache = {}
latest_artwork_time = 0

def sanitize_for_musicbrainz(text):
    """Clean up text for MusicBrainz search."""
    if not text:
        return ""
    # Remove special characters that affect search
    return re.sub(r'[^\w\s]', '', text).strip()

def fetch_from_musicbrainz(artist, album, title):
    """Search MusicBrainz and CoverArtArchive for album artwork."""
    global musicbrainz_cache, latest_artwork_time
    cache_key = f"{artist}|{album}"
    
    if cache_key in musicbrainz_cache:
        print(f"Using cached artwork for {artist} - {album}")
        return musicbrainz_cache[cache_key]
    
    print(f"Searching MusicBrainz for {artist} - {album}")
    
    headers = {
        'User-Agent': 'PrestoDeck-MPRIS (https://github.com/twij/PrestoDeck)'
    }

    time.sleep(1)

    if album and artist:
        try:
            clean_artist = sanitize_for_musicbrainz(artist)
            clean_album = sanitize_for_musicbrainz(album)

            search_url = f"https://musicbrainz.org/ws/2/release/?query=release:{clean_album}%20AND%20artist:{clean_artist}&fmt=json"
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('releases') and len(data['releases']) > 0:
                    release_id = data['releases'][0].get('id')
                    if release_id:
                        cover_url = f"https://coverartarchive.org/release/{release_id}/front"
                        time.sleep(1)
                        
                        img_response = requests.get(cover_url, headers=headers, timeout=5)
                        if img_response.status_code == 200:
                            art_data = resize_image(img_response.content)

                            if art_data:
                                if len(musicbrainz_cache) >= MUSICBRAINZ_CACHE_SIZE_LIMIT:
                                    random_key = random.choice(list(musicbrainz_cache.keys()))
                                    del musicbrainz_cache[random_key]
                                musicbrainz_cache[cache_key] = art_data

                                latest_artwork_time = time.time()
                                print("Setting latest_artwork_time after finding fresh art")
                                
                            return art_data
        except Exception as e:
            print(f"Error fetching from MusicBrainz: {e}")
    
    # Try artist only search as a fallback - maybe remove this as it's usually wrong
    if artist and not album:
        try:
            clean_artist = sanitize_for_musicbrainz(artist)
            
            search_url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{clean_artist}&fmt=json"
            response = requests.get(search_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('artists') and len(data['artists']) > 0:
                    artist_id = data['artists'][0].get('id')
                    if artist_id:
                        time.sleep(1)
                        releases_url = f"https://musicbrainz.org/ws/2/release?artist={artist_id}&limit=10&fmt=json"
                        releases_response = requests.get(releases_url, headers=headers, timeout=5)
                        
                        if releases_response.status_code == 200:
                            releases_data = releases_response.json()
                            if releases_data.get('releases') and len(releases_data['releases']) > 0:
                                for i in range(min(3, len(releases_data['releases']))):
                                    release_id = releases_data['releases'][i].get('id')
                                    if release_id:
                                        time.sleep(1)
                                        cover_url = f"https://coverartarchive.org/release/{release_id}/front"
                                        img_response = requests.get(cover_url, headers=headers, timeout=5)
                                        if img_response.status_code == 200:
                                            art_data = resize_image(img_response.content)
                                            if art_data:
                                                if len(musicbrainz_cache) >= MUSICBRAINZ_CACHE_SIZE_LIMIT:
                                                    random_key = random.choice(list(musicbrainz_cache.keys()))
                                                    del musicbrainz_cache[random_key]
                                                musicbrainz_cache[cache_key] = art_data

                                                latest_artwork_time = time.time()
                                                print("Setting latest_artwork_time after finding fresh art")
                                                
                                            return art_data
        except Exception as e:
            print(f"Error fetching artist art from MusicBrainz: {e}")
    
    return None

def get_latest_artwork_time():
    """Return the timestamp of when we last fetched fresh artwork."""
    global latest_artwork_time
    return latest_artwork_time

def reset_artwork_time():
    """Reset the artwork time counter."""
    global latest_artwork_time
    latest_artwork_time = 0