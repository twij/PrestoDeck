import gc
import time
import jpegdec
import pngdec
import uasyncio as asyncio
import urequests as requests

from touch import Button

from applications.spotify.spotify_client import Session, SpotifyWebApiClient
from base import BaseApp
import secrets

class State:
    """Tracks the current state of the Spotify app including playback and UI controls."""
    def __init__(self):
        self.toggle_leds = True
        self.is_playing = False
        self.repeat = False
        self.shuffle = False
        self.current_track = None
        self.show_controls = False
        self.latest_fetch = None
        self.exit = False

class ControlButton():
    """Represents a control button with an icon and touch area."""
    def __init__(self, display, name, icons, bounds, on_press=None, update=None):
        self.name = name
        self.enabled = False
        self.icon = icons[0] if icons else None
        self.pngs = {}
        if icons:
            for icon in icons:
                png = pngdec.PNG(display)
                png.open_file("applications/spotify/icons/" + icon)
                self.pngs[icon] = png

        self.button = Button(*bounds)
        self.on_press = on_press
        self.update = update

    def is_pressed(self, state):
        """Checks if the button is enabled and currently pressed."""
        return self.enabled and self.button.is_pressed()
    
    def draw(self, state):
        """Draws the button icon if enabled."""
        if self.enabled and self.icon:
            self.draw_icon()

    def draw_icon(self):
        """Renders the button's icon centered inside its bounds."""
        png = self.pngs[self.icon]
        x, y, width, height = self.button.bounds
        png_width, png_height = png.get_width(), png.get_height()
        x_offset = (width-png_width)//2
        y_offset = (height-png_height)//2

        png.decode(x+x_offset, y+y_offset)

class Spotify(BaseApp):
    """Main Spotify app managing playback controls, track display, and UI interactions."""
    def __init__(self):
        super().__init__(ambient_light=True, full_res=True, layers=2)

        self.display.set_layer(0)
        icon = pngdec.PNG(self.display)
        icon.open_file("applications/spotify/icon.png")
        icon.decode(self.center_x - icon.get_width()//2, self.center_y - icon.get_height()//2 - 20)
        self.presto.update()

        self.display.set_font("sans")
        self.display.set_layer(1)
        self.display_text("Connecting to WIFI", (90, self.height - 80), thickness=2)
        self.presto.update()

        self.presto.connect()
        while not self.presto.wifi.isconnected():
            self.clear(1)
            self.display_text("Failed to connect to WIFI", (40, self.height - 80), thickness=2)
            time.sleep(2)

        self.clear(1)
        self.display_text("Instantiating Spotify Client", (35, self.height - 80), thickness=2)
        self.spotify_client = self.get_spotify_client()
        self.clear(1)
        self.presto.update()

        # JPEG decoder
        self.j = jpegdec.JPEG(self.display)

        self.state = State()
        self.setup_buttons()
    
    def display_text(self, text, position, color=65535, scale=1, thickness=None):
        if thickness:
            self.display.set_thickness(2)
        x,y = position
        self.display.set_pen(color)
        self.display.text(text, x, y, scale=scale)
        self.presto.update()

    def get_spotify_client(self):
        if not hasattr(secrets, 'SPOTIFY_CREDENTIALS') or not secrets.SPOTIFY_CREDENTIALS:
            while True:
                self.clear(1)
                self.display.set_pen(self.colors.WHITE)
                self.display.text("Spotify credentials not found", 40, self.height - 80, scale=.9)
                self.presto.update()
                time.sleep(2)

        session = Session(secrets.SPOTIFY_CREDENTIALS)
        return SpotifyWebApiClient(session)
        
    def setup_buttons(self):
        """Initializes control buttons and their behavior."""
        # --- Shared update functions ---
        def update_show_controls(state, button):
            button.enabled = state.show_controls

        def update_always_enabled(state, button):
            button.enabled = True

        def update_play_pause(state, button):
            button.enabled = state.show_controls
            button.icon = "pause.png" if state.is_playing else "play.png"

        def update_shuffle(state, button):
            button.enabled = state.show_controls
            button.icon = "shuffle_on.png" if state.shuffle else "shuffle_off.png"

        def update_repeat(state, button):
            button.enabled = state.show_controls
            button.icon = "repeat_on.png" if state.repeat else "repeat_off.png"

        def update_light(state, button):
            button.enabled = state.show_controls
            button.icon = "light_on.png" if state.toggle_leds else "light_off.png"

        # --- On-press handlers ---
        def exit_app(self):
            self.state.exit = True

        def toggle_controls(self):
            self.state.show_controls = not self.state.show_controls

        def play_pause(self):
            if self.state.is_playing:
                self.spotify_client.pause()
            else:
                self.spotify_client.play()
            self.state.is_playing = not self.state.is_playing

        def next_track(self):
            self.spotify_client.next()
            self.state.latest_fetch = None

        def previous_track(self):
            self.spotify_client.previous()
            self.state.latest_fetch = None

        def toggle_shuffle(self):
            self.spotify_client.toggle_shuffle(not self.state.shuffle)
            self.state.shuffle = not self.state.shuffle

        def toggle_repeat(self):
            self.spotify_client.toggle_repeat(not self.state.repeat)
            self.state.repeat = not self.state.repeat

        def toggle_lights(self):
            self.toggle_leds(not self.state.toggle_leds)
            self.state.toggle_leds = not self.state.toggle_leds

        # --- Button configurations ---
        buttons_config = [
            ("Exit", ["exit.png"], (0, 0, 80, 80), exit_app, update_show_controls),
            ("Next", ["next.png"], (self.center_x + 60, self.height - 100, 80, 100), next_track, update_show_controls),
            ("Previous", ["previous.png"], (self.center_x - 140, self.height - 100, 80, 100), previous_track, update_show_controls),
            ("Play", ["play.png", "pause.png"], (self.center_x - 50, self.height - 100, 80, 100), play_pause, update_play_pause),
            ("Toggle Shuffle", ["shuffle_on.png", "shuffle_off.png"], (self.center_x - 230, self.height - 100, 80, 100), toggle_shuffle, update_shuffle),
            ("Toggle Repeat", ["repeat_on.png", "repeat_off.png"], (self.center_x + 150, self.height - 100, 80, 100), toggle_repeat, update_repeat),
            ("Toggle Light", ["light_on.png", "light_off.png"], (self.width - 100, 0, 100, 80), toggle_lights, update_light),
            ("Toggle Controls", None, (0, 0, self.width, self.height), toggle_controls, update_always_enabled),
        ]

        # --- Create ControlButton instances ---
        self.buttons = [
            ControlButton(self.display, name, icons, bounds, on_press, update)
            for name, icons, bounds, on_press, update in buttons_config
        ]

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

            for button in self.buttons:
                button.update(self.state, button)
                if button.is_pressed(self.state):
                    print(f"{button.name} pressed")
                    try:
                        button.on_press(self)
                    except Exception as e:
                        print(f"Failed to execute on_press: {e}")
                    break
            
            # Wait here until the user stops touching the screen
            while self.touch.state:
                self.touch.poll()

            await asyncio.sleep_ms(1)

    def show_image(self, img, minimized=False):
        """Displays an album cover image on the screen."""
        try:
            self.j.open_RAM(memoryview(img))

            img_width, img_height = self.j.get_width(), self.j.get_height()
            img_x, img_y = (self.width - img_width) // 2, (self.height - img_height) // 2

            self.clear(0)
            self.j.decode(img_x, img_y, jpegdec.JPEG_SCALE_FULL, dither=True)

        except OSError:
            print("Failed to load image.")
        
    def write_track(self):
        """Writes the track name and artists on the screen."""
        if self.state.current_track:
            self.display.set_thickness(3)

            track_name = self.state.current_track.get("name")
            # strip non-ascii characters
            track_name = ''.join(i if ord(i) < 128 else ' ' for i in track_name)
            if len(track_name) > 20:
                track_name = track_name[:20] + " ..."
            # shadow effect
            self.display.set_pen(self.colors._BLACK)
            self.display.text(track_name, 20, self.height - 137, scale=1.1)
            
            self.display.set_pen(self.colors.WHITE)
            self.display.text(track_name, 18, self.height - 140, scale=1.1)
            
            artists = ", ".join([artist.get("name") for artist in self.state.current_track.get("artists")])
            # strip non-ascii characters
            artists = ''.join(i if ord(i) < 128 else ' ' for i in artists)
            if len(artists) > 35:
                artists = artists[:35] + " ..."
            self.display.set_thickness(2)
            # shadow effect
            self.display.set_pen(self.colors._BLACK)
            self.display.text(artists, 20, self.height - 108, scale=0.7)
            
            self.display.set_pen(self.colors.WHITE)
            self.display.text(artists, 18, self.height - 111, scale=0.7)

    async def display_loop(self):
        """Periodically updates the display with the latest track info and controls."""
        INTERVAL = 10

        while not self.state.exit:
            update_display = False
            prev_track = self.state.current_track
            if not self.state.latest_fetch or time.time() - self.state.latest_fetch > INTERVAL:
                self.state.latest_fetch = time.time()
                result = fetch_state(self.spotify_client)
                if result:
                    device_id, self.state.current_track, self.state.is_playing, self.state.shuffle, self.state.repeat = result
                    if device_id:
                        self.spotify_client.session.device_id = device_id

            await asyncio.sleep(0)

            if not prev_track or prev_track.get("id") != self.state.current_track.get("id"):
                img = get_album_cover(self.state.current_track)
                self.show_image(img)

            await asyncio.sleep(0)

            self.clear(1)
            if self.state.show_controls:
                for button in self.buttons:
                    button.draw(self.state)
                self.write_track()

            self.presto.update()
            gc.collect()
            await asyncio.sleep_ms(200)

def fetch_state(spotify_client):
    """Fetches the current playback state from Spotify."""

    current_track = None
    is_playing = False
    shuffle = False
    repeat = False
    device_id = None
    try:
        resp = spotify_client.current_playing()
        if resp and resp.get("item"):
            current_track = resp["item"]
            is_playing = resp.get("is_playing")
            shuffle = resp.get("shuffle_state")
            repeat = resp.get("repeat_state", "off") != "off" 
            device_id = resp["device"]["id"]
            print("Got current playing track: " + current_track.get("name"))
    except Exception as e:
        print("Failed to get current playing track:", e)

    if not current_track:
        try:
            resp = spotify_client.recently_played()
            if resp and resp.get("items"):
                current_track = resp["items"][0]["track"]
                print("Got recently playing track: " + current_track.get("name"))
        except Exception as e:
            print("Failed to get recently played track:", e)

    if not current_track:
        return None

    return device_id, current_track, is_playing, shuffle, repeat

def get_album_cover(track):
    """Fetches and resizes the album cover image for the given track."""

    img_url = track["album"]["images"][1]["url"]
    
    img = None
    resize_url = f"https://wsrv.nl/?url={img_url}&w=480&h=480"
    try:
        response = requests.get(resize_url)
        if response.status_code == 200:
            img = response.content
        else:
            print("Failed to fetch image:", response.status_code)
    except Exception as e:
        print("Fetch image error:", e)
        
    return img

def launch():
    """Launches the Spotify app and starts the event loop."""
    app = Spotify()
    app.run()

    app.clear()
    del app
    gc.collect()