"""Shared text fitting, wrapping, and rendering helpers."""
from __future__ import annotations

import pygame

from engine.utilities.assets import AssetLoader


class TextRenderer:
    """Fits and draws text consistently across the game's UI."""

    def __init__(self, assets: AssetLoader) -> None:
        self.assets = assets

    def fit_font(
        self,
        value: str,
        font: pygame.font.Font,
        max_width: int,
        max_height: int,
    ) -> pygame.font.Font:
        for size in range(font.get_height(), 5, -1):
            candidate = self.assets.font(size)
            width, height = candidate.size(value)
            if width <= max_width and height <= max_height:
                return candidate
        return self.assets.font(6)

    def draw(
        self,
        screen: pygame.Surface,
        value: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
        center: bool = False,
        right: bool = False,
        max_width: int | None = None,
        max_height: int | None = None,
    ) -> None:
        if max_width is not None or max_height is not None:
            font = self.fit_font(
                value,
                font,
                max_width or screen.get_width(),
                max_height or screen.get_height(), 
            )
        image = font.render(value, True, color)
        rect = image.get_rect()
        if center:
            rect.center = position
        elif right:
            rect.midright = position
        else:
            rect.topleft = position
        screen.blit(image, rect)

    def draw_wrapped(
        self,
        screen: pygame.Surface,
        value: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        words = value.split()
        lines: list[str] = []
        fitted_font = font
        for size in range(font.get_height(), 5, -1):
            fitted_font = self.assets.font(size)
            lines = self._wrap_words(words, fitted_font, rect.width)
            if len(lines) * fitted_font.get_linesize() <= rect.height:
                break
        for index, line in enumerate(lines):
            if index * fitted_font.get_linesize() >= rect.height:
                break
            self.draw(
                screen,
                line,
                fitted_font,
                color,
                (rect.x, rect.y + index * fitted_font.get_linesize()),
                max_width=rect.width,
                max_height=fitted_font.get_linesize(),
            )

    @staticmethod
    def _wrap_words(words: list[str], font: pygame.font.Font, max_width: int) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines