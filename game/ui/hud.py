"""
HUD persistente: se dibuja encima de lo que sea que RoomManager haya
pintado, independiente de en qué room esté el jugador. Por ahora solo
muestra monedas y un prompt de interacción genérico; se ampliará cuando
haya llaves, detectores equipados, etc.
"""

from __future__ import annotations

from typing import Optional

import pygame

from game import config
from game.progression.economy import Economy


class HUD:
    def __init__(self, economy: Economy) -> None:
        self.economy = economy
        self._font = pygame.font.SysFont("arial", 22, bold=True)
        self._prompt_font = pygame.font.SysFont("arial", 16, bold=True)

    def draw(self, surface: pygame.Surface, active_prompt: Optional[str]) -> None:
        self._draw_coins(surface)
        if active_prompt is not None:
            self._draw_prompt(surface, active_prompt)

    def _draw_coins(self, surface: pygame.Surface) -> None:
        text = self._font.render(f"Monedas: {self.economy.coins}", True, config.COLOR_HUD_TEXT)
        padding = 10
        box = pygame.Rect(0, 0, text.get_width() + padding * 2, text.get_height() + padding * 2)
        box.topleft = (16, 16)

        bg = pygame.Surface(box.size)
        bg.fill(config.COLOR_HUD_BG)
        bg.set_alpha(150)
        surface.blit(bg, box.topleft)
        surface.blit(text, (box.x + padding, box.y + padding))

    def _draw_prompt(self, surface: pygame.Surface, prompt_text: str) -> None:
        text = self._prompt_font.render(
            f"[{config.INTERACT_KEY_NAME}] {prompt_text}", True, config.COLOR_PROMPT_TEXT
        )
        rect = text.get_rect()
        rect.centerx = config.SCREEN_WIDTH // 2
        rect.bottom = config.SCREEN_HEIGHT - 100
        surface.blit(text, rect)
# IRONEDIT:1783483891:8bd57287feb233b074aa84c076bf17fef1aa2ed8b0767e8c3fd2be5e3f357eed
