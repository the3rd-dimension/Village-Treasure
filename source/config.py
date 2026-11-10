"""Project-wide configuration."""
from pathlib import Path

#Directories
PROJECT_ROOT = Path(__file__).resolve().parent
CONTENT_DIR = PROJECT_ROOT / "content"
ASSETS_DIR = CONTENT_DIR / "assets"
DATA_DIR = CONTENT_DIR / "data"
MAPS_DIR = CONTENT_DIR / "maps"

#Display
GAME_TITLE = "The Village Treasure"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 540

#Performance
TARGET_FPS = 60
START_FULLSCREEN = False
START_VSYNC = True

#Debugging
LOG_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIRECTORY / "game.log"

#Colors
BACKGROUND_COLOR = (18, 18, 24)
PANEL_COLOR = (42, 44, 49)
PANEL_EDGE_COLOR = (180, 151, 94)
TEXT_COLOR_LIGHT = (244, 232, 203)
TEXT_COLOR_DARK = (18, 18, 24)
MUTED_COLOR = (171, 166, 146)
HIGHLIGHT_COLOR = (224, 185, 98)

#Fonts
DEFAULT_FONT_PATH = "fonts/PressStart2P-Regular.ttf"