"""Track information display for the MPRIS application."""

class TrackInfoDisplay:
    """Handles display of track title, artist, and album information."""
    
    def __init__(self, display, colors):
        """Initialize track info display.
        
        Args:
            display: The PrestoDeck display object
            colors: Display color palette
        """
        self.display = display
        self.colors = colors
    
    def write_track(self, track, show_controls=True):
        """Writes the track name and artists on the screen.
        
        Args:
            track: Track information dictionary
            show_controls: Whether controls are visible
        """
        if not show_controls or not track:
            return
            
        self.display.set_thickness(3)

        track_name = track.get("title", "Unknown")
        track_name = ''.join(i if ord(i) < 128 else ' ' for i in track_name)
        if len(track_name) > 20:
            track_name = track_name[:20] + " ..."
        
        self.display.set_pen(self.colors._BLACK)
        self.display.text(track_name, 20, self.display.height() - 137, scale=1.1)
        
        self.display.set_pen(self.colors.WHITE)
        self.display.text(track_name, 18, self.display.height() - 140, scale=1.1)
        
        artists = track.get("artist", "Unknown")
        artists = ''.join(i if ord(i) < 128 else ' ' for i in artists)
        if len(artists) > 35:
            artists = artists[:35] + " ..."
            
        self.display.set_thickness(2)
        self.display.set_pen(self.colors._BLACK)
        self.display.text(artists, 20, self.display.height() - 108, scale=0.7)
        
        self.display.set_pen(self.colors.WHITE)
        self.display.text(artists, 18, self.display.height() - 111, scale=0.7)