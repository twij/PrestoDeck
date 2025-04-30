# PrestoDeck

<img src="./docs/presto.jpg" />

PrestoDeck is a Spotify music controller for the Pimoroni Presto. It displays the album cover art, name, and artist of the currently playing track and provides basic controls for playback.

## Hardware

- [Pimoroni Presto](https://collabs.shop/xbvgb2)
- (Optional) [Right Angle USB C Cable](https://amzn.to/4jUYJ9F) 

## Installation 

Follow these steps to install and set up the project on your Presto:

### 1. Install Thonny
Download and install Thonny IDE, which you'll use to interact with your Presto and manage project files:
- [Download Thonny](https://thonny.org/)

### 2. Clone the GitHub Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/fatihak/PrestoDeck.git
```

### 3. Connect Presto to your computer with a USB-C cable

### 4. Upload Project Files
- Open **Thonny IDE**, and ensure the interpreter is set to **MicroPython (Raspberry Pi Pico)**.
- In the Files window, right clicking on the root of the cloned project in the Files window and selecting 'Upload to /' to copy all the files to the Presto

### 5. Store Wi-Fi Credentials
- In Thonny, open the `secrets.py` file.
- Replace the placeholder WIFI credentials with your SSID and password

### 6. Run the `main.py` Script
- In Thonny, open the `main.py` file.
- Click **Run** to launch the program. This will initiate the Spotify setup wizard.

### 7. Complete the Spotify Setup in Your Browser
- The setup wizard will display a URL on your presto.
- Navigate to the URL in your browser and follow the instructions to set up your Spotify credentials.

### 8. Copy Spotify Credentials to `credentials.py`
- After successfully setting up the Spotify integration, copy the **SPOTIFY_CREDENTIALS** (client ID, client secret, etc.) from the Thonny logs.
- Paste the credentials into the `credentials.py` file on the Presto.

## Additional Resources
- [Pimoroni Presto Github Repo](https://github.com/pimoroni/presto)
- [Getting Started with Pimoroni Presto](https://learn.pimoroni.com/article/getting-started-with-presto)
- [Micropython Spotify Web API](https://github.com/tltx/micropython-spotify-web-api)

## Sponsoring

PrestoDeck is maintained and developed with the help of sponsors. If you enjoy the project or find it useful, consider supporting its continued development.

<p align="center">
<a href="https://github.com/sponsors/fatihak" target="_blank"><img src="https://user-images.githubusercontent.com/345274/133218454-014a4101-b36a-48c6-a1f6-342881974938.png" alt="Become a Patreon" height="35" width="auto"></a>
<a href="https://www.patreon.com/akzdev" target="_blank"><img src="https://c5.patreon.com/external/logo/become_a_patron_button.png" alt="Become a Patreon" height="35" width="auto"></a>
<a href="https://www.buymeacoffee.com/akzdev" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="35" width="auto"></a>
</p>
