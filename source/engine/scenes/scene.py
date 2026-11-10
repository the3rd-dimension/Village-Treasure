"""Choice-driven Pygame scene for The Village Treasure."""
from __future__ import annotations

import pygame

from engine.graphics.transitions import LocationTransition
from engine.ui.cursor import Cursor
from engine.ui.text import TextRenderer
from engine.systems.game_state import ActionResult, GameState
from engine.utilities.assets import AssetLoader
from engine.utilities.logger import get_logger

import config

logger = get_logger("scene")
SCREEN_WIDTH = config.WINDOW_WIDTH
SCREEN_HEIGHT = config.WINDOW_HEIGHT
PANEL = config.PANEL_COLOR
PANEL_EDGE = config.PANEL_EDGE_COLOR
TEXT_LIGHT = config.TEXT_COLOR_LIGHT
TEXT_DARK = config.TEXT_COLOR_DARK
MUTED = config.MUTED_COLOR
HIGHLIGHT = config.HIGHLIGHT_COLOR
DIRECTION_KEYS = {
    pygame.K_w: "N",
    pygame.K_s: "S",
    pygame.K_a: "W",
    pygame.K_d: "E",
}
BUTTON_DIRECTIONS = {"W": "N", "S": "S", "A": "W", "D": "E"}


class AdventureScene:
    """Draws the interface and routes input to the game state."""

    def __init__(self, state: GameState, assets: AssetLoader) -> None:
        self.state = state
        self.assets = assets
        self.title_font = assets.font(42)
        self.header_font = assets.font(28)
        self.body_font = assets.font(20)
        self.small_font = assets.font(15)
        self.text_renderer = TextRenderer(assets)
        self.mode = "name"
        self.name_text = ""
        self.name_active = True
        pygame.key.start_text_input()
        self.action_index = 0
        self.dialogue_speaker = ""
        self.dialogue_lines: tuple[str, ...] = ()
        self.dialogue_index = 0
        self.toast = ""
        self.toast_time = 0.0
        self.transition = LocationTransition()
        self.cursor = Cursor(self.assets)
        self.pressed_direction: str | None = None
        self._background_key: tuple[str, tuple[int, int]] | None = None
        self._scaled_background: pygame.Surface | None = None
        self.action_rects: list[tuple[pygame.Rect, str]] = []
        self.slot_rects: list[pygame.Rect] = []
        self.nav_rects: dict[str, pygame.Rect] = {}
        self.name_rect = pygame.Rect(config.WINDOW_WIDTH // 2 - 400, config.WINDOW_HEIGHT // 2, 800, 60)
        self.start_rect = pygame.Rect(config.WINDOW_WIDTH // 2 - 150, config.WINDOW_HEIGHT // 2 + 75, 300, 54)
        self.restart_rect = pygame.Rect(470, 450, 160, 50)
        self.quit_rect = pygame.Rect(650, 450, 160, 50)

    @property
    def dialogue_open(self) -> bool:
        return bool(self.dialogue_lines)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.mode == "name":
            self._handle_name_event(event)
            return
        if self.transition.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)
            return
        if event.type != pygame.KEYDOWN:
            return

        if self.dialogue_open:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self._advance_dialogue()
            elif event.key == pygame.K_ESCAPE and not self.state.completed:
                self.dialogue_lines = ()
            return

        if self.state.completed:
            if event.key == pygame.K_RETURN:
                self._start_new_journey()
            return

        if event.key in DIRECTION_KEYS:
            self._navigate(DIRECTION_KEYS[event.key])
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            self._move_action_selection(-1 if event.key == pygame.K_UP else 1)
        elif event.key == pygame.K_RETURN:
            actions = self.state.actions()
            if actions:
                self._perform_action(actions[self.action_index][0])
        elif event.key == pygame.K_e:
            if any(action_id == "use_selected" for action_id, _ in self.state.actions()):
                self._perform_action("use_selected")
            else:
                self._set_toast("Select an item that can be used here.")
        elif event.key == pygame.K_TAB:
            self._select_next_item()
        elif pygame.K_1 <= event.key <= pygame.K_4:
            index = event.key - pygame.K_1
            items = self.state.inventory.items
            if index < len(items):
                self._select_item(items[index].id)

    def _handle_name_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.TEXTINPUT:
            if self.name_active and len(self.name_text) < 20:
                self.name_text += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name_text = self.name_text[:-1]
            elif event.key == pygame.K_RETURN:
                self._start_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_rect.collidepoint(event.pos):
                self._start_game()
            else:
                self.name_active = self.name_rect.collidepoint(event.pos)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.dialogue_open:
            self._advance_dialogue()
            return
        if self.state.completed:
            if self.restart_rect.collidepoint(position):
                self._start_new_journey()
            elif self.quit_rect.collidepoint(position):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        for rect, action_id in self.action_rects:
            if rect.collidepoint(position):
                self._perform_action(action_id)
                return
        for slot_index, rect in enumerate(self.slot_rects):
            if rect.collidepoint(position):
                items = self.state.inventory.items
                if slot_index < len(items):
                    self._select_item(items[slot_index].id)
                return
        for direction, rect in self.nav_rects.items():
            if rect.collidepoint(position):
                self._navigate(BUTTON_DIRECTIONS[direction])
                return

    def _start_game(self) -> None:
        result = self.state.start(self.name_text)
        self.mode = "game"
        pygame.key.stop_text_input()
        self._show_result(result)
        self._play_location_music()

    def _start_new_journey(self) -> None:
        self.state = GameState()
        self.mode = "game"
        self.action_index = 0
        self.toast = ""
        self.toast_time = 0.0
        self._show_result(self.state.start(self.name_text))
        self._play_location_music()

    def _perform_action(self, action_id: str) -> None:
        result = self.state.perform(action_id)
        self._show_result(result)
        if action_id.startswith("pickup:"):
            self.assets.play_sound("audio/sfx/item_pickup.wav")
        elif action_id == "use_selected":
            self.assets.play_sound("audio/sfx/item_use.wav")
        elif action_id == "open:chest":
            self.assets.play_sound("audio/sfx/chest_open.wav")
        elif action_id.startswith("talk:") or action_id.startswith("read:"):
            self.assets.play_sound("audio/sfx/dialogue.wav")

    def _show_result(self, result: ActionResult) -> None:
        if result.message:
            self._set_toast(result.message)
        if result.lines:
            self.dialogue_speaker = result.speaker
            self.dialogue_lines = result.lines
            self.dialogue_index = 0
        self.action_index = min(self.action_index, max(0, len(self.state.actions()) - 1))

    def _advance_dialogue(self) -> None:
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogue_lines):
            self.dialogue_lines = ()

    def _set_toast(self, message: str) -> None:
        self.toast = message
        self.toast_time = 4.0

    def _select_item(self, item_id: str) -> None:
        self._set_toast(self.state.select_item(item_id))
        self.assets.play_sound("audio/sfx/button_click.wav")
        self.action_index = 0

    def _select_next_item(self) -> None:
        items = self.state.inventory.items
        if not items:
            self._set_toast("Your bag is empty.")
            return
        selected_id = self.state.inventory.selected_id
        current_index = next(
            (index for index, item in enumerate(items) if item.id == selected_id),
            -1,
        )
        self._select_item(items[(current_index + 1) % len(items)].id)

    def _move_action_selection(self, amount: int) -> None:
        action_count = len(self.state.actions())
        if action_count:
            self.action_index = (self.action_index + amount) % action_count

    def _navigate(self, direction: str) -> None:
        destination = self.state.destination_for(direction)
        if destination is None:
            if self.state.location_id == "L12" and direction == "S":
                self._set_toast("The Treasure Gate is still locked.")
            else:
                self._set_toast("There is no path that way.")
            return
        self.pressed_direction = direction
        self.transition.start(destination)
        self.assets.play_sound("audio/sfx/button_click.wav")

    def update(self, delta_time: float) -> None:
        self.cursor.update()
        self.toast_time = max(0.0, self.toast_time - delta_time)
        destination = self.transition.update(delta_time)
        if destination is not None:
            if self.state.move_to(destination):
                self._play_location_music()
            else:
                logger.warning("Rejected transition to invalid destination %s.", destination)
                self._set_toast("You cannot travel there yet.")
        if not self.transition.active:
            self.pressed_direction = None
        self.action_index = min(self.action_index, max(0, len(self.state.actions()) - 1))

    def render(self, screen: pygame.Surface) -> None:
        if self.mode == "name":
            self._render_name_screen(screen)
            self.cursor.render(screen)
            return

        self._draw_location_background(screen)

        self._draw_location_header(screen)
        self._draw_inventory(screen)
        self._draw_navigation(screen)
        self._draw_actions(screen)
        self._draw_quest_and_status(screen)
        if self.dialogue_open:
            self._draw_dialogue(screen)
        if self.state.completed and not self.dialogue_open:
            self._draw_completion(screen)
        if self.transition.active:
            self._draw_transition(screen)

        self.cursor.render(screen)

    def _draw_location_background(self, screen: pygame.Surface) -> None:
        location = self.state.location
        image_path = location.background_image or location.background
        display_size = screen.get_size()
        background = self.assets.background(image_path) if image_path else None
        if background is None:
            self._background_key = None
            self._scaled_background = None
            screen.fill(config.BACKGROUND_COLOR)
            return

        key = (image_path, display_size)
        if key != self._background_key:
            self._scaled_background = pygame.transform.scale(background, display_size)
            self._background_key = key
        if self._scaled_background is not None:
            screen.blit(self._scaled_background, (0, 0))

    def _render_name_screen(self, screen: pygame.Surface) -> None:
        bg = self.assets.background("backgrounds/VillageTeasureMainMenu.png")
        if bg:
            screen.blit(pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        else:
            screen.fill(config.BACKGROUND_COLOR)

        title_panel = pygame.Rect(160, 25, 960, 68)
        subtitle_panel = pygame.Rect(220, 100, 840, 50)
        prompt_panel = pygame.Rect(400, 315, 480, 40)
        instruction_panel = pygame.Rect(350, config.WINDOW_HEIGHT - 75, 580, 42)

        self._draw_panel(screen, title_panel, (39, 39, 40))
        self._draw_text(
            screen,
            config.GAME_TITLE,
            self.title_font,
            TEXT_LIGHT,
            title_panel.center,
            center=True,
            max_width=title_panel.width - 24,
            max_height=title_panel.height - 12,
        )
        self._draw_panel(screen, subtitle_panel, (39, 39, 40))
        self._draw_text(
            screen,
            "NCC Assignment for L3DC10 - Roll#1001591",
            self.body_font,
            TEXT_LIGHT,
            subtitle_panel.center,
            center=True,
            max_width=subtitle_panel.width - 24,
            max_height=subtitle_panel.height - 12,
        )
        self._draw_panel(screen, prompt_panel, (39, 39, 40))
        self._draw_text(
            screen,
            "Enter your name",
            self.body_font,
            HIGHLIGHT,
            prompt_panel.center,
            center=True,
            max_width=prompt_panel.width - 24,
            max_height=prompt_panel.height - 10,
        )
        self._draw_panel(screen, self.name_rect, (51, 52, 47))
        shown_name = self.name_text or "Traveler"
        self._draw_text(
            screen,
            shown_name,
            self.header_font,
            TEXT_LIGHT if self.name_text else MUTED,
            self.name_rect.center,
            center=True,
            max_width=self.name_rect.width - 24,
            max_height=self.name_rect.height - 12,
        )
        self._draw_button(screen, self.start_rect, "Begin Journey", True, True)
        self._draw_panel(screen, instruction_panel, (39, 39, 40))
        self._draw_text(
            screen,
            "Type a name and press Enter",
            self.small_font,
            TEXT_LIGHT,
            instruction_panel.center,
            center=True,
            max_width=instruction_panel.width - 24,
            max_height=instruction_panel.height - 10,
        )

    def _draw_location_header(self, screen: pygame.Surface) -> None:
        location_label = self.state.location.name
        if self.state.location_id == "L10" and self.state.in_mill_storage:
            location_label += " — Storage"
        rect = pygame.Rect(402, 18, 476, 58)
        self._draw_panel(screen, rect, (54, 51, 45))
        self._draw_text(
            screen,
            location_label.upper(),
            self.header_font,
            TEXT_LIGHT,
            rect.center,
            True,
            max_width=rect.width - 24,
            max_height=rect.height - 12,
        )

    def _draw_inventory(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(18, 129, 196, 319)
        self._draw_panel(screen, panel)
        self._draw_text(
            screen,
            "INVENTORY",
            self.body_font,
            TEXT_LIGHT,
            (panel.centerx, panel.y + 20),
            True,
            max_width=panel.width - 20,
            max_height=32,
        )
        self._draw_text(screen, f"{len(self.state.inventory.items)}/4", self.small_font, MUTED, (panel.right - 27, panel.y + 40), True)
        self.slot_rects = []
        for index in range(4):
            rect = pygame.Rect(panel.x + 13, panel.y + 53 + index * 62, panel.width - 26, 53)
            self.slot_rects.append(rect)
            item = self.state.inventory.items[index] if index < len(self.state.inventory.items) else None
            selected = item is not None and item.id == self.state.inventory.selected_id
            self._draw_panel(screen, rect, (75, 72, 63) if selected else (49, 51, 53), selected)
            if item is None:
                self._draw_text(
                    screen,
                    "Empty slot",
                    self.small_font,
                    MUTED,
                    rect.center,
                    True,
                    max_width=rect.width - 12,
                    max_height=rect.height - 8,
                )
                continue
            icon = self.assets.image_if_available(item.icon, (36, 36))
            if icon is not None:
                screen.blit(icon, (rect.x + 7, rect.y + 8))
            else:
                self._draw_item_icon(screen, item, pygame.Rect(rect.x + 7, rect.y + 8, 36, 36))
            self._draw_text(
                screen,
                item.name,
                self.small_font,
                TEXT_LIGHT,
                (rect.x + 51, rect.y + 13),
                max_width=rect.width - 59,
                max_height=20,
            )
            self._draw_text(
                screen,
                "Selected" if selected else f"Press {index + 1}",
                self.small_font,
                HIGHLIGHT if selected else MUTED,
                (rect.x + 51, rect.y + 32),
                max_width=rect.width - 59,
                max_height=16,
            )

    def _draw_item_icon(self, screen: pygame.Surface, item, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, item.color, rect)
        pygame.draw.rect(screen, (39, 39, 37), rect, 2)
        initials = "".join(word[0] for word in item.name.split()[:2])
        self._draw_text(screen, initials, self.small_font, (35, 34, 30), rect.center, True)

    def _draw_navigation(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(18, 466, 196, 224)
        self._draw_panel(screen, panel)
        self._draw_text(
            screen, "TRAVEL", self.body_font, TEXT_LIGHT,
            (panel.centerx, panel.y + 21), True,
            max_width=panel.width - 20, max_height=28,
        )
        self._draw_text(
            screen, "WASD or click", self.small_font, MUTED,
            (panel.centerx, panel.y + 43), True,
            max_width=panel.width - 20, max_height=18,
        )
        self.nav_rects = {
            "W": pygame.Rect(panel.x + 61, panel.y + 68, 37, 37),
            "A": pygame.Rect(panel.x + 17, panel.y + 112, 37, 37),
            "S": pygame.Rect(panel.x + 61, panel.y + 112, 37, 37),
            "D": pygame.Rect(panel.x + 105, panel.y + 112, 37, 37),
        }
        labels = {"W": "W", "S": "S", "A": "A", "D": "D"}
        exits = self.state.exits()
        for key, rect in self.nav_rects.items():
            direction = BUTTON_DIRECTIONS[key]
            enabled = direction in exits
            self._draw_button(
                screen,
                rect,
                labels[key],
                enabled,
                selected=direction == self.pressed_direction,
                compact=True,
            )

    def _draw_actions(self, screen: pygame.Surface) -> None:
        panel = pygame.Rect(970, 129, 292, 561)
        self._draw_panel(screen, panel)
        self._draw_text(
            screen,
            "ACTIONS",
            self.body_font,
            TEXT_LIGHT,
            (panel.centerx, panel.y + 22),
            True,
            max_width=panel.width - 24,
            max_height=30,
        )
        self.action_rects = []
        actions = self.state.actions()
        self.action_index = min(self.action_index, max(0, len(actions) - 1))
        if not actions:
            self._draw_text(
                screen,
                "Nothing to do here.",
                self.small_font,
                MUTED,
                (panel.centerx, panel.y + 75),
                True,
                max_width=panel.width - 24,
            )
        for index, (action_id, label) in enumerate(actions):
            rect = pygame.Rect(panel.x + 16, panel.y + 54 + index * 50, panel.width - 32, 42)
            self.action_rects.append((rect, action_id))
            self._draw_button(screen, rect, label, True, index == self.action_index)
        self._draw_text(
            screen,
            "↑ / ↓ choose | Enter act |  E use item",
            self.small_font,
            MUTED,
            (panel.centerx, panel.bottom - 24),
            True,
            max_width=panel.width - 24,
            max_height=20,
        )

    def _draw_quest_and_status(self, screen: pygame.Surface) -> None:
        quest_rect = pygame.Rect(235, 620, 720, 31)
        self._draw_panel(screen, quest_rect, (43, 45, 43))
        self._draw_text(
            screen,
            f"QUEST  {self.state.quest_step}",
            self.small_font,
            HIGHLIGHT,
            (quest_rect.x + 12, quest_rect.y + 8),
            max_width=quest_rect.width - 24,
            max_height=quest_rect.height - 6,
        )
        status_rect = pygame.Rect(235, 658, 720, 36)
        self._draw_panel(screen, status_rect, (40, 42, 44))
        if self.toast_time > 0:
            self._draw_text(
                screen,
                self.toast,
                self.small_font,
                TEXT_LIGHT,
                (status_rect.x + 12, status_rect.y + 10),
                max_width=status_rect.width - 24,
                max_height=status_rect.height - 8,
            )
        else:
            self._draw_text(
                screen,
                "Click an item to inspect it. Use Tab to select the next item.",
                self.small_font,
                MUTED,
                (status_rect.x + 12, status_rect.y + 10),
                max_width=status_rect.width - 24,
                max_height=status_rect.height - 8,
            )

    def _draw_dialogue(self, screen: pygame.Surface) -> None:
        rect = pygame.Rect(252, 430, 686, 174)
        self._draw_panel(screen, rect, (39, 39, 40))
        portrait_rect = pygame.Rect(rect.x + 14, rect.y + 17, 74, 92)
        speaker = self.dialogue_speaker.casefold()
        character = self.state.characters.get(speaker)
        if character is None:
            character = next(
                (
                    value
                    for value in self.state.characters.values()
                    if str(value.get("name", "")).casefold() == speaker
                ),
                None,
            )

        if character is None:
            sprite = "sprites/player/player.png"
            color = (120, 120, 120)
        else:
            sprite = str(character.get("sprite", ""))
            color_values = character.get("color", [120, 120, 120])
            color = (color_values[0], color_values[1], color_values[2])
        portrait = self.assets.image(sprite, portrait_rect.size, color)
        screen.blit(portrait, portrait_rect)

        self._draw_text(
            screen,
            self.dialogue_speaker,
            self.body_font,
            HIGHLIGHT,
            (rect.x + 105, rect.y + 18),
            max_width=rect.width - 125,
            max_height=28,
        )
        line = self.dialogue_lines[self.dialogue_index]
        self._draw_wrapped(screen, line, self.body_font, TEXT_LIGHT, pygame.Rect(rect.x + 105, rect.y + 49, 552, 77))
        self._draw_text(
            screen,
            "Enter / Space / click to continue",
            self.small_font,
            MUTED,
            (rect.right - 16, rect.bottom - 23),
            right=True,
            max_width=rect.width - 120,
            max_height=20,
        )

    def _draw_completion(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 15, 16, 190))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(330, 260, 620, 270)
        self._draw_panel(screen, panel, (48, 45, 38))
        self._draw_text(
            screen, "WILLOWMERE'S STORY IS COMPLETE", self.header_font,
            HIGHLIGHT, (panel.centerx, panel.y + 64), True,
            max_width=panel.width - 32, max_height=40,
        )
        self._draw_text(
            screen, "Thank you for discovering the village's true treasure.",
            self.body_font, TEXT_LIGHT, (panel.centerx, panel.y + 112), True,
            max_width=panel.width - 32, max_height=32,
        )
        self._draw_button(screen, self.restart_rect, "New Journey", True, True)
        self._draw_button(screen, self.quit_rect, "Quit", True)

    def _draw_transition(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.transition.alpha))
        screen.blit(overlay, (0, 0))
        if self.transition.phase == "hold" and self.transition.destination:
            name = self.state.world.get(self.transition.destination).name
            self._draw_text(
                screen, name, self.header_font, TEXT_LIGHT,
                (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), True,
                max_width=SCREEN_WIDTH - 80, max_height=48,
            )

    def _draw_panel(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        fill: tuple[int, int, int] = PANEL,
        selected: bool = False,
    ) -> None:
        pygame.draw.rect(screen, fill, rect)
        border = HIGHLIGHT if selected else PANEL_EDGE
        pygame.draw.rect(screen, border, rect, 2)

    def _draw_button(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        enabled: bool,
        selected: bool = False,
        compact: bool = False,
    ) -> None:
        fill = (80, 83, 72) if enabled else (48, 49, 49)
        if selected and enabled:
            fill = (100, 91, 66)
        pygame.draw.rect(screen, fill, rect)
        color = TEXT_LIGHT if enabled else MUTED
        pygame.draw.rect(screen, HIGHLIGHT if selected and enabled else PANEL_EDGE, rect, 2)
        font = self.small_font if compact or len(label) > 20 else self.body_font
        self._draw_text(
            screen,
            label,
            font,
            color,
            rect.center,
            True,
            max_width=rect.width - 12,
            max_height=rect.height - 8,
        )

    def _fit_font(
        self,
        value: str,
        font: pygame.font.Font,
        max_width: int,
        max_height: int,
    ) -> pygame.font.Font:
        return self.text_renderer.fit_font(value, font, max_width, max_height)

    def _draw_text(
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
        self.text_renderer.draw(
            screen,
            value,
            font,
            color,
            position,
            center,
            right,
            max_width,
            max_height,
        )

    def _draw_wrapped(
        self,
        screen: pygame.Surface,
        value: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        self.text_renderer.draw_wrapped(screen, value, font, color, rect)

    def _play_location_music(self) -> None:
        track = self.state.location.music
        self.assets.play_music(track)