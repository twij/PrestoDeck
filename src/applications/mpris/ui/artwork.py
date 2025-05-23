"""Artwork display handling for the MPRIS application."""
from applications.mpris.utils.image_decoder import ImageHandler

class ArtworkDisplay:
    """Manages display of album artwork."""
    
    def __init__(self, display, colors, app=None):
        """Initialize artwork display.
        
        Args:
            display: The PrestoDeck display object
            colors: Display color palette
            app: Reference to the application for dimensions access
        """
        self.display = display
        self.colors = colors
        self.image_handler = ImageHandler(display)
        
        self.image_handler.app = app
        
        self.current_art_data = None
        self.current_etag = None
    
    def show_artwork(self, art_data, force=False):
        """Display album artwork on the screen.
        
        Args:
            art_data: Binary artwork data
            force: Whether to force redisplay even if unchanged
            
        Returns:
            True if artwork was updated, False otherwise
        """
        if not art_data:
            self._show_placeholder()
            return False
            
        if not force and self.current_art_data is art_data:
            print("Skipping artwork update - no change detected")
            return False
            
        self.display.set_layer(0)
        self.clear_layer()
        success = self.image_handler.show_image(art_data)
        
        if success:
            self.current_art_data = art_data
            return True
        else:
            self._show_placeholder()
            return False
    
    def clear_layer(self):
        """Clear the artwork layer."""
        self.display.set_pen(0)
        
        display_width = 480
        display_height = 480
        
        self.display.rectangle(0, 0, display_width, display_height)
    
    def _show_placeholder(self, track=None):
        """Show a dark background with track title."""
        self.clear_layer()
        
        if track:
            title = track.get('title', 'Unknown')
            self.display.set_pen(self.colors.WHITE)
            self.display.text("♫ " + title, 20, 120, scale=1.2)
        
        print("Displayed basic placeholder image")