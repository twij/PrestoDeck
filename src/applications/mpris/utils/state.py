"""State management for the MPRIS application."""

class State:
    """Tracks the current state of the MPRIS app including playback and UI controls."""
    def __init__(self):
        self.toggle_leds = True
        self.is_playing = False
        self.track = None
        self.show_controls = False
        self.exit = False
        self.available_players = []
        self.current_player = None
        self.latest_fetch = None
        self.force_refresh = False
        
        self.strict_privacy = True
    
    def copy(self):
        """Create a copy of the state for comparison."""
        state = State()
        state.toggle_leds = self.toggle_leds
        state.is_playing = self.is_playing
        state.show_controls = self.show_controls
        state.exit = self.exit
        state.available_players = self.available_players.copy() if self.available_players else []
        state.current_player = self.current_player
        state.latest_fetch = self.latest_fetch
        state.force_refresh = self.force_refresh
        state.strict_privacy = self.strict_privacy
        
        if self.track:
            state.track = {'id': self.track.get('id')}
        return state
    
    def __eq__(self, other):
        """Compare states for equality, used to detect changes."""
        if not isinstance(other, State) or other is None:
            return False
        
        track_id_match = False
        if self.track and other.track:
            track_id_match = self.track.get('id') == other.track.get('id')
        elif self.track is None and other.track is None:
            track_id_match = True
            
        return (
            self.toggle_leds == other.toggle_leds and
            self.is_playing == other.is_playing and
            self.show_controls == other.show_controls and
            self.exit == other.exit and
            self.current_player == other.current_player and
            track_id_match
        )