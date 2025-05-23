"""Configuration settings for the MPRIS server."""
import os
import secrets as crypto_secrets

MPRIS_SERVICE_PREFIX = "org.mpris.MediaPlayer2."

# Player priority order - players earlier in the list will be preferred
PLAYER_PRIORITY = [
    "musikcube",
    "firefox",
    "vlc",
    "spotify",
    "chromium",
    # Add other players you use...
]

PRIORITIZE_PLAYING = True

MUSICBRAINZ_CACHE_SIZE_LIMIT = 250
ART_CACHE_SIZE_LIMIT = 20

DEFAULT_ARTWORK_SIZE = (480, 480)


TOKEN_FILE = os.path.expanduser("~/.config/prestodeck/token")
CERT_FILE = os.path.expanduser("~/.config/cert.pem")
KEY_FILE = os.path.expanduser("~/.config/key.pem")

DEFAULT_PORT = 5000

# Get or generate API token
def get_api_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    else:
        token_dir = os.path.dirname(TOKEN_FILE)
        if not os.path.exists(token_dir):
            os.makedirs(token_dir, exist_ok=True)
            print(f"Created directory: {token_dir}")
        
        token = crypto_secrets.token_hex(16)

        with open(TOKEN_FILE, 'w') as f:
            f.write(token)

        os.chmod(TOKEN_FILE, 0o600)
        return token

current_player = None