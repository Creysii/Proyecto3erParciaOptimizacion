"""
DetectorSelectMenu: overlay que se abre al pisar un portal de función ya
desbloqueado. Muestra los algoritmos que el jugador tiene desbloqueados,
navegable con teclado, y al confirmar dispara on_select(algorithm_id).

ESC cancela sin disparar nada (el jugador se queda en el lobby).
"""

from __future__ import annotations

from typing import Callable

import pygame

from game import config
from game.data.algorithms_config import get_algorithm_config
from game.ui.overlay import Overlay


class DetectorSelectMenu(Overlay):
    def __init__(
        self,
        function_id: str,
        function_name: str,
        unlocked_algorithm_ids: list[str],
        on_select: Callable[[str], None],
    ) -> None:
        self.function_id = function_id
        self.function_name = function_name
        self.unlocked_algorithm_ids = unlocked_algorithm_ids
        self.on_select = on_select

        self.selected_index = 0
        self._done = False

        self._title_font = pygame.font.SysFont("arial", 24, bold=True)
        self._item_font = pygame.font.SysFont("arial", 20)
        self._hint_font = pygame.font.SysFont("arial", 14)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self._done = True
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(self.unlocked_algorithm_ids)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(self.unlocked_algorithm_ids)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            chosen_id = self.unlocked_algorithm_ids[self.selected_index]
            self._done = True
            self.on_select(chosen_id)

    def update(self, dt: float) -> None:
        return

    def is_done(self) -> bool:
        return self._done

    def draw(self, surface: pygame.Surface) -> None:
        overlay_bg = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay_bg.fill((0, 0, 0))
        overlay_bg.set_alpha(180)
        surface.blit(overlay_bg, (0, 0))

        box_width, box_height = 380, 90 + 34 * len(self.unlocked_algorithm_ids)
        box = pygame.Rect(0, 0, box_width, box_height)
        box.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        pygame.draw.rect(surface, (30, 30, 40), box, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 210), box, width=2, border_radius=8)

        title = self._title_font.render(f"Elige detector — {self.function_name}", True, (255, 255, 255))
        surface.blit(title, (box.x + 20, box.y + 16))

        for i, algo_id in enumerate(self.unlocked_algorithm_ids):
            algo = get_algorithm_config(algo_id)
            y = box.y + 60 + i * 34
            is_selected = i == self.selected_index
            color = (255, 230, 120) if is_selected else (220, 220, 220)
            prefix = "> " if is_selected else "  "
            text = self._item_font.render(f"{prefix}{algo.name}", True, color)
            surface.blit(text, (box.x + 30, y))

        hint = self._hint_font.render(
            "↑↓ mover · Enter confirmar · Esc cancelar", True, (170, 170, 170)
        )
        surface.blit(hint, (box.x + 20, box.bottom - 26))
# IRONEDIT:1783483891:a7a4667e5906c4e2bc12f3925c712665eced1a8a4c671b59b2ac18d968cb8633
