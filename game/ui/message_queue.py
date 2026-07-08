"""
Cola simple de mensajes temporales en pantalla. Deliberadamente tonta:
solo guarda un texto y un tiempo de vida, y se autolimpia. La usamos tanto
para "Work in progress" al pisar el portal del nivel 1, como para los
mensajes de costo al interactuar con un gate bloqueado — evita duplicar
la lógica de "texto flotante temporal" en dos lugares distintos.
"""

from __future__ import annotations

from typing import Optional

import pygame

from game import config


class MessageQueue:
    def __init__(self) -> None:
        self.current_message: Optional[str] = None
        self._timer: float = 0.0
        self._font = pygame.font.SysFont("arial", 22, bold=True)

    def show(self, text: str, duration: float = 2.0) -> None:
        self.current_message = text
        self._timer = duration

    def update(self, dt: float) -> None:
        if self.current_message is None:
            return
        self._timer -= dt
        if self._timer <= 0:
            self.current_message = None

    def draw(self, surface: pygame.Surface) -> None:
        if self.current_message is None:
            return

        text_surf = self._font.render(self.current_message, True, config.COLOR_MESSAGE_TEXT)
        padding = 14
        box_width = text_surf.get_width() + padding * 2
        box_height = text_surf.get_height() + padding * 2

        box = pygame.Surface((box_width, box_height))
        box.fill(config.COLOR_MESSAGE_BG)
        box.set_alpha(210)

        box_rect = box.get_rect()
        box_rect.centerx = config.SCREEN_WIDTH // 2
        box_rect.bottom = config.SCREEN_HEIGHT - 40

        surface.blit(box, box_rect)
        surface.blit(text_surf, (box_rect.x + padding, box_rect.y + padding))
# IRONEDIT:1783483891:5443bf4405525e5f361a1f450ad2661f0ba1328302ec815b1c065eb5792d143a
