"""MPRIS DBus interface for communicating with media players."""
import os
import time
import random
import urllib.parse
import dbus
from config import MPRIS_SERVICE_PREFIX, PLAYER_PRIORITY, PRIORITIZE_PLAYING, current_player, ART_CACHE_SIZE_LIMIT
from utils.image_utils import resize_image, generate_placeholder_art, encode_image_base64
from utils.musicbrainz import fetch_from_musicbrainz

art_file_cache = {}

def get_player_by_id(player_id):
    """Get DBus player object by ID."""
    try:
        bus = dbus.SessionBus()
        player_obj = bus.get_object(player_id, '/org/mpris/MediaPlayer2')
        
        try:
            props_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
            props_interface.Get('org.mpris.MediaPlayer2', 'Identity')
            return player_obj
        except dbus.exceptions.DBusException as e:
            print(f"Player {player_id} is not responding: {e}")
            return None
            
    except dbus.exceptions.DBusException as e:
        if "org.freedesktop.DBus.Error.ServiceUnknown" in str(e):
            print(f"Player {player_id} is no longer available")
        else:
            print(f"Error getting player {player_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting player {player_id}: {e}")
        return None

def get_available_players():
    """Get all available MPRIS players."""
    global players_cache
    
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        dbus_interface = dbus.Interface(obj, 'org.freedesktop.DBus')
        
        players = []
        for service in dbus_interface.ListNames():
            if service.startswith('org.mpris.MediaPlayer2.'):
                try:
                    player_obj = bus.get_object(service, '/org/mpris/MediaPlayer2')
                    props_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
                    
                    identity = str(props_interface.Get('org.mpris.MediaPlayer2', 'Identity'))
                    
                    players.append({
                        'id': service,
                        'name': identity
                    })
                except Exception as e:
                    print(f"Error getting player info for {service}: {e}")
        
        players_cache = players
        return players
    except Exception as e:
        print(f"Error listing players: {e}")
        return players_cache

def get_priority_sorted_players():
    """Get available players sorted by priority."""
    players = get_available_players()

    if PRIORITIZE_PLAYING:
        for player in players:
            try:
                player_obj = get_player_by_id(player['id'])
                if player_obj:
                    props_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
                    status = str(props_interface.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
                    if status == 'Playing':
                        print(f"Found actively playing player: {player['id']}")
                        return [player]
            except Exception as e:
                print(f"Error checking play status for {player['id']}: {e}")
    
    def get_priority(player):
        player_id = player['id']
        for i, prefix in enumerate(PLAYER_PRIORITY):
            if player_id.startswith(MPRIS_SERVICE_PREFIX + prefix):
                return i
        return 999  # Low priority for unlisted players
    
    return sorted(players, key=get_priority)

def get_media_info(player_id=None):
    """Get media info from the specified or current player."""
    global current_player
    
    available_players = get_available_players()
    available_player_ids = [p['id'] for p in available_players]
    
    if current_player and current_player not in available_player_ids:
        print(f"Player {current_player} is no longer available")
        current_player = None
    
    if not player_id and not current_player:
        priority_players = get_priority_sorted_players()
        if priority_players:
            current_player = priority_players[0]['id']
            print(f"Auto-switching to priority player: {current_player}")
        else:
            print("No available players found")
            return None
    
    player_id = player_id or current_player
    
    if player_id not in available_player_ids:
        print(f"Player {player_id} is not available")
        return None
    
    player_obj = get_player_by_id(player_id)
    
    if not player_obj:
        print(f"Failed to get player object for {player_id}")
        if player_id == current_player:
            current_player = None
        return None
    
    try:
        props_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
        playback_status = str(props_interface.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        metadata = props_interface.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        
        track_id = str(metadata.get('mpris:trackid', '')) or str(time.time())
        
        artists = metadata.get('xesam:artist', ['Unknown'])
        if isinstance(artists, dbus.Array):
            artist = ', '.join([str(a) for a in artists])
        else:
            artist = str(artists)
        
        title = str(metadata.get('xesam:title', 'Unknown'))
        album = str(metadata.get('xesam:album', 'Unknown'))
        
        art_data = None
        art_url = metadata.get('mpris:artUrl', '')
        if art_url:
            art_url = str(art_url)
            if art_url.startswith('file://'):
                # Local file - decode URL-encoded characters
                try:
                    file_path = urllib.parse.unquote(art_url[7:])

                    if file_path in art_file_cache:
                        if not hasattr(get_media_info, 'logged_cache_files'):
                            get_media_info.logged_cache_files = set()
                        
                        if file_path not in get_media_info.logged_cache_files:
                            print(f"Using cached art for file: {file_path}")
                            get_media_info.logged_cache_files.add(file_path)
                        art_data = art_file_cache[file_path]
                    else:
                        print(f"Trying to load art from file: {file_path}")
                        
                        # Special handling for Firefox - maybe we can remove this now?
                        if 'firefox' in file_path.lower():
                            max_attempts = 3
                            for attempt in range(max_attempts):
                                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                    try:
                                        with open(file_path, 'rb') as f:
                                            image_data = f.read()
                                            art_data = resize_image(image_data)
                                            if art_data:
                                                print(f"Successfully loaded Firefox art on attempt {attempt+1}")
                                                break
                                    except Exception as e:
                                        print(f"Attempt {attempt+1} failed: {e}")
                                
                                if attempt < max_attempts - 1:
                                    print(f"Retrying Firefox art in 0.5 seconds...")
                                    time.sleep(0.5)
                            
                            if not art_data:
                                print("All attempts to load Firefox art failed, trying alternatives")
                        else:
                            if not os.path.exists(file_path):
                                print(f"File does not exist: {file_path}")
                                raise FileNotFoundError(f"File not found: {file_path}")
                                
                            if not os.access(file_path, os.R_OK):
                                print(f"File is not readable: {file_path}")
                                raise PermissionError(f"Cannot read file: {file_path}")
                                
                            file_size = os.path.getsize(file_path)
                            if file_size == 0:
                                print(f"File is empty: {file_path}")
                                raise ValueError(f"Empty file: {file_path}")
                                
                            print(f"File exists and is readable, size: {file_size} bytes")
                            
                            with open(file_path, 'rb') as f:
                                image_data = f.read()
                                print(f"Successfully read {len(image_data)} bytes from file")
                                art_data = resize_image(image_data)
                                if art_data is None:
                                    print(f"Failed to resize image from {file_path}")
                    
                        if art_data:
                            if len(art_file_cache) >= ART_CACHE_SIZE_LIMIT:
                                random_key = random.choice(list(art_file_cache.keys()))
                                del art_file_cache[random_key]
                            art_file_cache[file_path] = art_data
                            print(f"Cached art for file: {file_path}")
                except Exception as e:
                    print(f"Error loading art from file {art_url}: {e}")
            elif art_url.startswith(('http://', 'https://')):
                from utils.image_utils import fetch_art_from_url
                art_data = fetch_art_from_url(art_url)

        if not art_data:
            print(f"No local art found, trying MusicBrainz for {artist} - {album} - {title}")
            art_data = fetch_from_musicbrainz(artist, album, title)
            if art_data:
                print("Found artwork from MusicBrainz!")

        if not art_data:
            print("No artwork found, using placeholder")
            try:
                placeholder_data = generate_placeholder_art(f"{title[:20]}")
                if placeholder_data:
                    art_data = placeholder_data
            except Exception as e:
                print(f"Failed to create placeholder: {e}")
                art_data = None

        art_data_base64 = encode_image_base64(art_data)
        
        return {
            'id': track_id,
            'artist': artist,
            'title': title,
            'album': album,
            'playing': playback_status == 'Playing',
            'playback_status': playback_status,
            'art_url': art_url,
            'art_data': art_data_base64,
            'is_base64': True
        }
    
    except Exception as e:
        print(f"Error getting media info: {e}")
        if player_id == current_player:
            current_player = None
        return None

def get_media_state_for_etag():
    """Get a lightweight state representation for ETag calculation."""
    global current_player
    
    if not current_player:
        return "no_player"
    
    try:
        player_obj = get_player_by_id(current_player)
        if not player_obj:
            return "invalid_player"
            
        props_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
        metadata = props_interface.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        track_id = str(metadata.get('mpris:trackid', '')) 
        art_url = str(metadata.get('mpris:artUrl', ''))
        playback_status = str(props_interface.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus'))
        
        state = f"{current_player}|{track_id}|{art_url}|{playback_status}"
        return state
    except Exception as e:
        print(f"Error getting lightweight state: {e}")
        return "error_state"

players_cache = []