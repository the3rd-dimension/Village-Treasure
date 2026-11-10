"""Optional asset loading with safe, reusable fallbacks."""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import pygame

import config
from engine.audio.audio_manager import AudioManager
from engine.utilities.logger import get_logger

logger = get_logger("assets")


class AssetLoader:
    """Loads available assets and returns placeholders for missing files."""

    def __init__(self, assets_dir: Path | None = None) -> None:
        self.assets_dir = assets_dir or config.ASSETS_DIR
        self._png_decoder = self._load_png_decoder()
        self._images: dict[tuple[str, tuple[int, int] | None], pygame.Surface | None] = {}
        self._backgrounds: dict[str, pygame.Surface | None] = {}
        self._fonts: dict[tuple[str | None, int], pygame.font.Font] = {}
        self.audio = AudioManager(self.assets_dir)

    @staticmethod
    def _load_png_decoder() -> object | None:
        if sys.platform != "win32":
            return None
        package_dir = Path(pygame.__file__).resolve().parent
        decoder_path = package_dir / "libpng16-16.dll"
        if not decoder_path.is_file():
            return None
        try:
            return ctypes.WinDLL(str(decoder_path))
        except OSError as error:
            logger.warning("Could not load PNG decoder %s: %s", decoder_path, error)
            return None

    def exists(self, relative_path: str) -> bool:
        return (self.assets_dir / relative_path).is_file()

    def image_if_available(self, relative_path: str, size: tuple[int, int], ) -> pygame.Surface | None:
        if not self.exists(relative_path):
            return None
        return self.image(relative_path, size)

    def image(self, relative_path: str, size: tuple[int, int] | None = None, color: tuple[int, int, int] = (96, 91, 83)) -> pygame.Surface:
        key = (relative_path, size)
        if key not in self._images:
            path = self.assets_dir / relative_path
            image: pygame.Surface | None = None
            if path.is_file():
                try:
                    image = pygame.image.load(str(path)).convert_alpha()
                    if size is not None:
                        image = pygame.transform.scale(image, size)
                except (pygame.error, OSError) as error:
                    logger.warning("Could not load image %s: %s", path, error)
            self._images[key] = image

        loaded = self._images[key]
        if loaded is not None:
            return loaded
        placeholder_size = size or (64, 64)
        placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
        placeholder.fill(color)
        pygame.draw.rect(placeholder, (40, 35, 33), placeholder.get_rect(), 3)
        return placeholder

    def background(self, relative_path: str) -> pygame.Surface | None:
        if relative_path not in self._backgrounds:
            path = self.assets_dir / relative_path
            image: pygame.Surface | None = None
            if path.is_file():
                try:
                    image = pygame.image.load(str(path)).convert()
                except (pygame.error, OSError) as error:
                    logger.warning("Could not load background %s: %s", path, error)
            self._backgrounds[relative_path] = image
        return self._backgrounds[relative_path]

    def font(self, size: int, relative_path: str = config.DEFAULT_FONT_PATH) -> pygame.font.Font:
        key = (relative_path, size)
        if key not in self._fonts:
            path = self.assets_dir / relative_path
            try:
                self._fonts[key] = (
                    pygame.font.Font(str(path), size)
                    if path.is_file()
                    else pygame.font.Font(None, size)
                )
            except (pygame.error, OSError) as error:
                logger.warning("Could not load font %s: %s", path, error)
                self._fonts[key] = pygame.font.Font(None, size)
        return self._fonts[key]

    def play_music(self, relative_path: str, loops: int = -1) -> bool:
        return self.audio.play_music(relative_path, loops)

    def sound(self, relative_path: str) -> pygame.mixer.Sound | None:
        return self.audio.get_sound(relative_path)

    def play_sound(self, relative_path: str) -> bool:
        return self.audio.play_sound(relative_path)
