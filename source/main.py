from __future__ import annotations

import pygame

from engine.core.clock import GameClock
from engine.core.events import EventManager
from engine.core.settings import GameSettings
from engine.scenes.scene import AdventureScene
from engine.systems.game_state import GameState
from engine.utilities.assets import AssetLoader
from engine.utilities.logger import get_logger


logger = get_logger("startup")


def main() -> int:
    """Initialize Pygame"""
    settings = GameSettings.from_project_config()

    try:
        pygame.init()

        flags = pygame.FULLSCREEN if settings.fullscreen else 0
        screen = pygame.display.set_mode((settings.window_width, settings.window_height), flags, vsync=1 if settings.vsync else 0)
        pygame.display.set_caption(settings.title)

        clock = GameClock(settings.target_fps)
        event_manager = EventManager()

        logger.info("Application initialized.")
        logger.info(
            "Window: %s x %s | Target FPS: %s",
            settings.window_width,
            settings.window_height,
            settings.target_fps,
        )

        assets = AssetLoader()
        state = GameState()
        scene = AdventureScene(state, assets)
        running = True
        while running:
            delta_time = clock.tick()

            for event in event_manager.poll():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    scene.handle_event(event)

            if not running:
                continue

            scene.update(delta_time)
            scene.render(screen)
            pygame.display.flip()

        logger.info("Application shutdown requested.")
        return 0

    except Exception:
        logger.exception("A fatal error occurred while running the game.")
        return 1

    finally:
        pygame.quit()
        logger.info("Pygame has been shut down.")


if __name__ == "__main__":
    raise SystemExit(main())