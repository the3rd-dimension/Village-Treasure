"""Audio management system for the game."""
from __future__ import annotations

import pygame
from pathlib import Path
from engine.utilities.logger import get_logger

logger = get_logger("audio")

class AudioManager:
    """Handles music and sound effect playback."""

    def __init__(self, assets_dir: Path) -> None:
        self.assets_dir = assets_dir
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        self._current_music: str | None = None

    def play_music(self, relative_path: str, loops: int = -1) -> bool:
        """Loads and plays a music track."""
        if pygame.mixer.get_init() is None:
            return False

        path = self.assets_dir / relative_path
        if not path.is_file():
            if self._current_music is not None:
                pygame.mixer.music.stop()
                self._current_music = None
            return False

        try:
            if self._current_music == relative_path and pygame.mixer.music.get_busy():
                return True
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(loops)
            self._current_music = relative_path
            return True
        except pygame.error as error:
            logger.warning("Could not play music %s: %s", path, error)
            return False

    def get_sound(self, relative_path: str) -> pygame.mixer.Sound | None:
        """Loads a sound into memory and returns it."""
        if relative_path not in self._sounds:
            path = self.assets_dir / relative_path
            if not path.is_file() or pygame.mixer.get_init() is None:
                self._sounds[relative_path] = None
            else:
                try:
                    self._sounds[relative_path] = pygame.mixer.Sound(str(path))
                except (pygame.error, OSError) as error:
                    logger.warning("Could not load sound %s: %s", path, error)
                    self._sounds[relative_path] = None
        return self._sounds[relative_path]

    def play_sound(self, relative_path: str) -> bool:
        """Plays a sound effect once."""
        sound = self.get_sound(relative_path)
        if sound is None:
            return False
        try:
            sound.play()
            return True
        except pygame.error as error:
            logger.warning("Could not play sound %s: %s", relative_path, error)
            return False
