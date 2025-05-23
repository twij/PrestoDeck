"""MPRIS application for PrestoDeck."""
import gc
import time
import pngdec
import uasyncio as asyncio
import secrets

from base import BaseApp
from applications.mpris.api.mpris_api import MPRISApiClient
from applications.mpris.utils.state import State
from applications.mpris.ui.controls import ControlsManager
from applications.mpris.ui.track_info import TrackInfoDisplay
from applications.mpris.ui.artwork import ArtworkDisplay

class MPRIS(BaseApp):
    """Main MPRIS app managing playback controls, track display, and UI interactions."""
    def __init__(self):
        super().__init__(ambient_light=True, full_res=True, layers=2)

        self.display.set_layer(0)
        self.clear(0)
        self.display.set_layer(1)
        self.clear(1)

        self.display.set_layer(0)
        icon = pngdec.PNG(self.display)
        # i dont have an icon but i guess spotify's is nice enough
        icon.open_file("applications/spotify/icon.png")
        icon.decode(self.center_x - icon.get_width()//2, self.center_y - icon.get_height()//2 - 20)
        
        self.display.set_font("sans")
        self.display.set_layer(1)
        self.display_text("Connecting to WIFI", (90, self.height - 80), thickness=2)
        self.presto.update()

        self.presto.connect()
        while not self.presto.wifi.isconnected():
            self.clear(1)
            self.display_text("Failed to connect to WIFI", (40, self.height - 80), thickness=2)
            time.sleep(2)

        self.state = State()
        
        self.clear(1)
        self.display_text("Connecting to MPRIS server", (35, self.height - 80), thickness=2)
        self.mpris_client = self.get_mpris_client()
        self.clear(1)
        self.presto.update()
        
        self.controls = ControlsManager(self)
        self.track_info = TrackInfoDisplay(self.display, self.colors)
        self.artwork = ArtworkDisplay(self.display, self.colors, app=self)
    
    def display_text(self, text, position, color=65535, scale=1, thickness=None):
        """Helper to display text on the screen."""
        if thickness:
            self.display.set_thickness(2)
        x,y = position
        self.display.set_pen(color)
        self.display.text(text, x, y, scale=scale)
        self.presto.update()

    def get_mpris_client(self):
        """Initialize the MPRIS client with server URL and token from secrets."""
        if not hasattr(secrets, 'MPRIS_SERVER_URL') or not secrets.MPRIS_SERVER_URL:
            while True:
                self.clear(1)
                self.display.set_pen(self.colors.WHITE)
                self.display.text("MPRIS server URL not found", 40, self.height - 80, scale=.9)
                self.display.text("Add MPRIS_SERVER_URL to secrets.py", 40, self.height - 40, scale=.9)
                self.presto.update()
                time.sleep(2)

        api_token = None
        if hasattr(secrets, 'MPRIS_API_TOKEN'):
            api_token = secrets.MPRIS_API_TOKEN
        else:
            self.clear(1)
            self.display.set_pen(self.colors.YELLOW)
            self.display.text("Warning: No API token found", 40, self.height - 80, scale=.9)
            self.display.text("Add MPRIS_API_TOKEN to secrets.py", 40, self.height - 40, scale=.9)
            self.presto.update()
            time.sleep(2)

        return MPRISApiClient(secrets.MPRIS_SERVER_URL, api_token, self.state.strict_privacy)

    def run(self):
        """Starts the app's event loops."""
        loop = asyncio.get_event_loop()
        loop.create_task(self.touch_handler_loop())
        loop.create_task(self.display_loop())
        loop.run_forever()

    async def touch_handler_loop(self):
        """Handles touch input events and button presses."""
        while not self.state.exit:
            self.touch.poll()

            button_pressed = self.controls.handle_touch(self.state)
            
            if not button_pressed and self.touch.state:
                self.state.show_controls = not self.state.show_controls
                print(f"Controls toggled to {self.state.show_controls}")
                self.state.force_refresh = True
            
            while self.touch.state:
                self.touch.poll()

            await asyncio.sleep_ms(1)

    def update_ui(self):
        """Update the UI based on current state."""
        self.display.set_layer(1)
        self.clear(1)
        
        if self.state.show_controls:
            print("Drawing controls")
            self.controls.draw_controls(self.state)
            self.track_info.write_track(self.state.track, self.state.show_controls)
        
        print("Updating display")
        self.presto.update()

    async def display_loop(self):
        """Periodically updates the display with the latest track info and controls."""
        INTERVAL = 5
        
        prev_state = None
        first_run = True
        
        while not self.state.exit:
            force_refresh = first_run or self.state.force_refresh
            
            if force_refresh:
                print(f"Forcing refresh - reason: {'first run' if first_run else 'manual request'}")
            
            current_time = time.time()
            if force_refresh or not self.state.latest_fetch or current_time - self.state.latest_fetch > INTERVAL:
                self.state.latest_fetch = current_time
                self.state.force_refresh = False
                
                try:
                    media_info = self.mpris_client.get_current_media(force=force_refresh)
                    
                    if media_info and isinstance(media_info, dict):
                        if 'track' in media_info:
                            self.state.track = media_info['track']
                            
                        if 'playback_status' in media_info:
                            self.state.is_playing = media_info['playback_status'] == 'playing'
                        
                        if 'art_data' in media_info and media_info['art_data']:
                            artwork_updated = self.artwork.show_artwork(
                                media_info['art_data'], 
                                force=first_run
                            )
                            if artwork_updated:
                                self.presto.update()
                    
                except Exception as e:
                    print(f"Error fetching media info: {e}")
                    import sys
                    sys.print_exception(e)
                    
                if first_run:
                    self.state.show_controls = False
                    print("First run - controls hidden by default")
                    
            if first_run or prev_state is None or prev_state != self.state:
                self.update_ui()
                
                prev_state = self.state.copy()
                
            if first_run:
                first_run = False
                print("First run completed")
                
            gc.collect()
            await asyncio.sleep_ms(200)

def launch():
    """Launches the MPRIS app and starts the event loop."""
    app = MPRIS()
    app.run()

    app.clear()
    del app
    gc.collect()