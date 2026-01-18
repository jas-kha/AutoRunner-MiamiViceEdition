import os
from scripts import APP_NAME, APP_PUBLISHER

BASE_DIR = os.path.join(
    os.getenv("APPDATA"),
    APP_PUBLISHER,
    APP_NAME
)

RECENT_FILE = os.path.join(BASE_DIR, "recent.json")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

os.makedirs(BASE_DIR, exist_ok=True)
