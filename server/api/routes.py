"""API routes for the MPRIS server."""
import json
import hashlib
import dbus
from flask import jsonify, request
from modules.auth import require_auth
from modules.dbus_interface import (
    get_media_info, get_player_by_id, get_available_players, 
    get_priority_sorted_players
)
from config import current_player

def register_routes(app):
    """Register API routes with the Flask app."""
    
    @app.route('/artwork', methods=['GET'])
    @require_auth
    def get_artwork():
        """API endpoint to get just the current artwork."""
        if_none_match = request.headers.get('If-None-Match')

        media_info = get_media_info()
        
        if media_info and media_info.get('art_data'):
            art_data = media_info['art_data']

            hash_value = hashlib.md5(art_data.encode('utf-8')).hexdigest()
            
            if if_none_match and if_none_match == hash_value:
                return '', 304  # Not Modified
            
            response = jsonify({'art_data': art_data, 'is_base64': True})
            response.headers['ETag'] = hash_value
            response.headers['Cache-Control'] = 'private, max-age=0'
            return response
        else:
            return jsonify({"error": "No artwork available"}), 404

    @app.route('/current', methods=['GET'])
    @require_auth
    def current_media():
        """API endpoint to get current media info."""
        include_art = request.args.get('include_art', 'true').lower() != 'false'
        
        if_none_match = request.headers.get('If-None-Match')
        if if_none_match:
            print(f"Client sent If-None-Match: {if_none_match} for current")
        
        media_info = get_media_info()
        
        if not media_info:
            priority_players = get_priority_sorted_players()
            if priority_players:
                for player in priority_players:
                    current_player = player['id']
                    print(f"Trying priority player: {current_player}")
                    media_info = get_media_info()
                    if media_info:
                        print(f"Successfully selected player: {current_player}")
                        break
        
        if media_info:
            if not include_art and 'art_data' in media_info:
                media_info['art_data'] = None
            
            response_data = json.dumps(media_info)
            etag = hashlib.md5(response_data.encode()).hexdigest()
            
            if if_none_match and if_none_match == etag:
                return '', 304
            
            response = jsonify(media_info)
            response.headers['ETag'] = etag
            response.headers['Cache-Control'] = 'private, max-age=0'
            return response
        else:
            return jsonify({"error": "No media info available", "no_media": True}), 404

    @app.route('/players', methods=['GET'])
    @require_auth
    def list_players():
        """API endpoint to list available players."""
        players = get_available_players()
        return jsonify(players)

    @app.route('/select_player/<player_id>', methods=['POST'])
    @require_auth
    def select_player(player_id):
        """API endpoint to select a player."""
        global current_player
        
        if player_id in [p['id'] for p in get_available_players()]:
            current_player = player_id
            return jsonify({"success": True, "current_player": current_player})
        else:
            return jsonify({"error": "Player not found"}), 404

    @app.route('/play', methods=['POST'])
    @require_auth
    def play():
        """API endpoint to send play command."""
        global current_player
        try:
            if not current_player:
                priority_players = get_priority_sorted_players()
                if priority_players:
                    current_player = priority_players[0]['id']
                    print(f"Auto-selected player: {current_player}")
                else:
                    return jsonify({"error": "No available players found"}), 404

            player_obj = get_player_by_id(current_player)
            if player_obj:
                player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
                player_interface.Play()
                return jsonify({"success": True})
            return jsonify({"error": "No player selected"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/pause', methods=['POST'])
    @require_auth
    def pause():
        """API endpoint to send pause command."""
        global current_player
        try:
            if not current_player:
                priority_players = get_priority_sorted_players()
                if priority_players:
                    current_player = priority_players[0]['id']
                    print(f"Auto-selected player: {current_player}")
                else:
                    return jsonify({"error": "No available players found"}), 404

            player_obj = get_player_by_id(current_player)
            if player_obj:
                player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
                player_interface.Pause()
                return jsonify({"success": True})
            return jsonify({"error": "No player selected"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/next', methods=['POST'])
    @require_auth
    def next_track():
        """API endpoint to send next track command."""
        global current_player
        try:
            if not current_player:
                priority_players = get_priority_sorted_players()
                if priority_players:
                    current_player = priority_players[0]['id']
                    print(f"Auto-selected player: {current_player}")
                else:
                    return jsonify({"error": "No available players found"}), 404

            player_obj = get_player_by_id(current_player)
            if player_obj:
                player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
                print(f"Sending Next command to player: {current_player}")
                try:
                    player_interface.Next()
                    return jsonify({"success": True})
                except dbus.exceptions.DBusException as dbus_error:
                    if "is not available now" in str(dbus_error):
                        print(f"Next function not available for {current_player}: {dbus_error}")
                        return jsonify({"error": "Next function not available", "details": str(dbus_error)}), 400
                    raise
            return jsonify({"error": "No player selected"}), 400
        except Exception as e:
            print(f"Error on next track: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/previous', methods=['POST'])
    @require_auth
    def previous_track():
        """API endpoint to send previous track command."""
        global current_player
        try:
            if not current_player:
                priority_players = get_priority_sorted_players()
                if priority_players:
                    current_player = priority_players[0]['id']
                    print(f"Auto-selected player: {current_player}")
                else:
                    return jsonify({"error": "No available players found"}), 404

            player_obj = get_player_by_id(current_player)
            if player_obj:
                player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')
                player_interface.Previous()
                return jsonify({"success": True})
            return jsonify({"error": "No player selected"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/playpause', methods=['POST'])
    @require_auth
    def play_pause():
        """API endpoint to toggle play/pause state."""
        global current_player
        try:
            if not current_player:
                priority_players = get_priority_sorted_players()
                if priority_players:
                    current_player = priority_players[0]['id']
                    print(f"Auto-selected player: {current_player}")
                else:
                    return jsonify({"error": "No available players found"}), 404

            player_obj = get_player_by_id(current_player)
            if player_obj:
                properties_interface = dbus.Interface(player_obj, 'org.freedesktop.DBus.Properties')
                playback_status = properties_interface.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
                
                player_interface = dbus.Interface(player_obj, 'org.mpris.MediaPlayer2.Player')

                if playback_status == 'Playing':
                    player_interface.Pause()
                    print(f"Pausing player: {current_player}")
                else:
                    player_interface.Play()
                    print(f"Playing player: {current_player}")
                    
                return jsonify({"success": True, "action": "pause" if playback_status == 'Playing' else "play"})
            return jsonify({"error": "No player selected"}), 400
        except Exception as e:
            print(f"Error toggling playback: {e}")
            return jsonify({"error": str(e)}), 500
            
    return app