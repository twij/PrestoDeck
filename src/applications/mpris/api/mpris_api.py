"""MPRIS API client for communicating with an MPRIS server."""
import time
import ubinascii
from applications.mpris.network.client import CachingClient

class MPRISApiClient:
    """API client for MPRIS-specific endpoints."""
    
    def __init__(self, server_url, api_token=None, strict_privacy=True):
        """Initialize MPRIS API client.
        
        Args:
            server_url: MPRIS server URL
            api_token: Optional API token for authentication
            strict_privacy: Whether to enforce HTTPS
        """
        self.client = CachingClient(server_url, api_token, strict_privacy)
        self.first_boot_completed = False
        self.last_track_id = None
    
    def get_current_media(self, force=False):
        """Get current media info with separate art handling for memory efficiency.
        
        Args:
            force: Whether to force a fresh request
            
        Returns:
            Dict with current media information
        """

        if not self.first_boot_completed:
            print("First boot detected - forcing fresh data")
            self.first_boot_completed = True
            force = True
            self.client.etag_cache.clear()
        
        try:
            meta_endpoint = "current?include_art=false" 
            result = self.client.make_request(meta_endpoint, force=force)
            
            if result and isinstance(result, dict) and 'error' not in result:
                try:
                    track_changed = False
                    current_track_id = None
                    if 'track' in result and result['track']:
                        current_track_id = result['track'].get('id')
                        
                    if self.last_track_id and self.last_track_id != current_track_id:
                        if current_track_id and self.last_track_id:
                            print(f"Track changed from {self.last_track_id} to {current_track_id}")
                            track_changed = True
                            print("Clearing all ETags due to track change")
                            self.client.etag_cache.clear()
                            force = True
                    
                    if current_track_id:
                        self.last_track_id = current_track_id
                    
                    art_endpoint = "artwork"
                    print(f"Fetching artwork - force={force or track_changed}")
                    art_result = self.client.make_request(art_endpoint, force=force or track_changed)
                    if art_result and isinstance(art_result, dict) and 'art_data' in art_result:
                        art_data = art_result.get('art_data')
                        
                        if art_data and isinstance(art_data, str) and not ('from_304_cache' in art_result):
                            try:
                                print(f"Converting base64 string to binary data, length: {len(art_data)}")
                                art_data = ubinascii.a2b_base64(art_data)
                                print(f"Successfully decoded base64 data to {len(art_data)} bytes")
                                art_result['art_data'] = art_data
                                self.client.binary_cache["artwork"] = (time.time(), art_data)
                            except Exception as e:
                                print(f"Error decoding base64 data: {e}")
                                import sys
                                sys.print_exception(e)
                        
                        if art_data:
                            result['art_data'] = art_data
                            
                except Exception as e:
                    print(f"Error handling track change: {e}")
                    import sys
                    sys.print_exception(e)
            
            return result
        except Exception as e:
            print(f"Error fetching media info: {e}")
            import sys
            sys.print_exception(e)
            return {"error": f"Failed to get media info: {e}"}
    
    def get_players(self, force=False):
        """Get available players with optional force refresh."""
        return self.client.make_request("players", force=force)
    
    def play(self):
        """Sends play command to server."""
        try:
            response = self.client.make_request('/play', 'POST')
            return response.status_code == 200
        except Exception as e:
            print(f"Play command failed: {e}")
            return False

    def pause(self):
        """Sends pause command to server."""
        try:
            response = self.client.make_request('/pause', 'POST')
            return response.status_code == 200
        except Exception as e:
            print(f"Pause command failed: {e}")
            return False

    def play_pause(self):
        """Toggles play/pause state."""
        try:
            result = self.client.make_request('/playpause', 'POST')
            return result.get('success', False) if isinstance(result, dict) else False
        except Exception as e:
            print(f"PlayPause toggle failed: {e}")
            return False

    def next(self):
        """Sends next track command to server."""
        try:
            result = self.client.make_request('/next', 'POST')
            return result.get('success', False) if isinstance(result, dict) else False
        except Exception as e:
            print(f"Next track command failed: {e}")
            return False

    def previous(self):
        """Sends previous track command to server."""
        try:
            result = self.client.make_request('/previous', 'POST')
            return result.get('success', False) if isinstance(result, dict) else False
        except Exception as e:
            print(f"Previous track command failed: {e}")
            return False
    
    def select_player(self, player_id):
        """Send command to change the player."""
        res = self.client.make_request(f"select_player/{player_id}", method="POST")
        self.client.last_check["current"] = 0
        return res