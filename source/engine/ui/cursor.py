import pygame
from engine.utilities.assets import AssetLoader
from engine.utilities.logger import get_logger

logger = get_logger("cursor")

class Cursor:
    def __init__(self, assets: AssetLoader) -> None:
        self.assets = assets
        self.relative_path = "cursor/Cursor Default.png"
        self.image = self.assets.image(self.relative_path, size=None)
        self.hotspot = (0, 0)
        self.pos = (0, 0)
        pygame.mouse.set_visible(False)

    def update(self) -> None:
        self.pos = pygame.mouse.get_pos()

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, (self.pos[0] - self.hotspot[0], self.pos[1] - self.hotspot[1]))
