"""UI controls and buttons for the MPRIS application."""
import pngdec
from touch import Button

class ControlButton:
    """Represents a control button with an icon and touch area."""
    def __init__(self, display, name, icons, bounds, on_press=None, update=None):
        """Initialize a control button.
        
        Args:
            display: The PrestoDeck display object
            name: Button name for identification
            icons: List of icon filenames
            bounds: (x, y, width, height) for button position
            on_press: Callback function when button is pressed
            update: Function to update button state
        """
        self.name = name
        self.enabled = False
        self.icon = icons[0] if icons else None
        self.pngs = {}
        if icons:
            for icon in icons:
                png = pngdec.PNG(display)
                # Use the Spotify icons folder for now
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


class ControlsManager:
    """Manages all control buttons for the application."""
    
    def __init__(self, app):
        """Initialize controls manager.
        
        Args:
            app: The MPRIS application instance
        """
        self.app = app
        self.display = app.display
        self.buttons = []
        self.setup_buttons()
    
    def setup_buttons(self):
        """Initializes control buttons and their behavior."""
        def update_show_controls(state, button):
            button.enabled = state.show_controls

        def update_always_enabled(state, button):
            button.enabled = True

        def update_play_pause(state, button):
            button.enabled = state.show_controls
            button.icon = "pause.png" if state.is_playing else "play.png"

        def update_light(state, button):
            button.enabled = state.show_controls
            button.icon = "light_on.png" if state.toggle_leds else "light_off.png"


        def exit_app(self):
            self.app.state.exit = True

        def toggle_controls(self):
            self.app.state.show_controls = not self.app.state.show_controls
            print(f"Controls toggled: {self.app.state.show_controls}")

        def play_pause(self):
            if self.app.state.is_playing:
                self.app.mpris_client.pause()
            else:
                self.app.mpris_client.play()
            self.app.state.is_playing = not self.app.state.is_playing
            self.app.state.force_refresh = True
            self.app.state.latest_fetch = 0

        def next_track(self):
            self.app.mpris_client.next()
            self.app.state.force_refresh = True
            self.app.state.latest_fetch = 0

        def previous_track(self):
            self.app.mpris_client.previous()
            self.app.state.force_refresh = True
            self.app.state.latest_fetch = 0

        def toggle_lights(self):
            self.app.toggle_leds(not self.app.state.toggle_leds)
            self.app.state.toggle_leds = not self.app.state.toggle_leds

        display_width = self.app.width
        display_height = self.app.height
        center_x = display_width // 2
        
        buttons_config = [
            ("Exit", ["exit.png"], (0, 0, 80, 80), exit_app, update_show_controls),
            ("Next", ["next.png"], (center_x + 60, display_height - 100, 80, 100), next_track, update_show_controls),
            ("Previous", ["previous.png"], (center_x - 140, display_height - 100, 80, 100), previous_track, update_show_controls),
            ("Play", ["play.png", "pause.png"], (center_x - 50, display_height - 100, 80, 100), play_pause, update_play_pause),
            ("Toggle Light", ["light_on.png", "light_off.png"], (display_width - 100, 0, 100, 80), toggle_lights, update_light),
            ("Toggle Controls", None, (0, 0, display_width, display_height), toggle_controls, update_always_enabled),
        ]

        self.buttons = [
            ControlButton(self.display, name, icons, bounds, 
                          lambda self=self.app, handler=on_press: handler(self), 
                          update)
            for name, icons, bounds, on_press, update in buttons_config
        ]
    
    def handle_touch(self, state):
        """Handle touch events for all buttons.
        
        Args:
            state: Current application state
            
        Returns:
            True if a button was pressed, False otherwise
        """
        for button in self.buttons:
            button.update(state, button)
            
        for button in self.buttons:
            if button.is_pressed(state):
                print(f"{button.name} pressed")
                try:
                    button.on_press()
                except Exception as e:
                    print(f"Failed to execute on_press: {e}")
                return True
        
        return False
    
    def draw_controls(self, state):
        """Draw all control buttons on the screen.
        
        Args:
            state: Current application state
        """
        self.display.set_pen(0)
        self.display.rectangle(0, self.display.height() - 150, self.display.width(), 150)
        
        for button in self.buttons:
            button.update(state, button)
            button.draw(state)