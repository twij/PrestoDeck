"""Background monitor thread for MPRIS players."""
import time
import threading
from config import current_player
from modules.dbus_interface import get_available_players, get_priority_sorted_players

def player_monitor_thread():
    """Background thread that periodically checks if players are available."""
    global current_player
    
    while True:
        try:
            if current_player:
                available_players = get_available_players()
                available_player_ids = [p['id'] for p in available_players]
                
                if current_player not in available_player_ids:
                    print(f"Player {current_player} is no longer available")
                    current_player = None
                    
                    priority_players = get_priority_sorted_players()
                    if priority_players:
                        current_player = priority_players[0]['id']
                        print(f"Auto-switched to priority player: {current_player}")
            
            time.sleep(5)
            
        except Exception as e:
            print(f"Error in player monitor: {e}")
            time.sleep(10)

def start_monitor_thread():
    """Start the player monitor thread."""
    monitor_thread = threading.Thread(target=player_monitor_thread, daemon=True)
    monitor_thread.start()
    return monitor_thread