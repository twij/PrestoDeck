try:
    from env_loader import load_env
    env = load_env()
except ImportError:
    print("env_loader not found. Using fallback values.")
    env = {}

WIFI_SSID = env.get('WIFI_SSID', "")
WIFI_PASSWORD = env.get('WIFI_PASSWORD', "")

MPRIS_API_TOKEN = env.get('MPRIS_API_TOKEN', "")
MPRIS_SERVER_URL = env.get('MPRIS_SERVER_URL', "")

SPOTIFY_CLIENT_ID = env.get('SPOTIFY_CLIENT_ID', "")
SPOTIFY_CLIENT_SECRET = env.get('SPOTIFY_CLIENT_SECRET', "")

if not WIFI_SSID or not WIFI_PASSWORD:
    print("WARNING: WIFI credentials not found in .env file")

