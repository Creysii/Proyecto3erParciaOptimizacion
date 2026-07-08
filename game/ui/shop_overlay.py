"""
ShopOverlay: overlay de compra, mismo patrón que DetectorSelectMenu
(pausa la room activa, captura su propio input, se dibuja encima).

Deliberadamente recibe TRES closures en vez de una referencia directa a
Economy/Unlocks — mantiene el mismo principio de acoplamiento mínimo que
ya aplicamos en RoomContext/Interactable: este overlay no necesita saber
qué es una Economy ni cómo funciona, solo "cómo pedir el saldo actual" y
"cómo intentar comprar un ítem", que es exactamente lo que necesita.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pygame

from game import config
from game.ui.overlay import Overlay


@dataclass
class ShopItem:
    id: str
    name: str
    kind_label: str  # "Función" | "Algoritmo" — puramente para mostrar
    price: int
    unlocked: bool


class ShopOverlay(Overlay):
    def __init__(
        self,
        get_items: Callable[[], list[ShopItem]],
        get_balance: Callable[[], int],
        attempt_purchase: Callable[[ShopItem], bool],
    ) -> None:
        self.get_items = get_items
        self.get_balance = get_balance
        self.attempt_purchase = attempt_purchase

        self.selected_index = 0
        self._done = False
        self._feedback_message: Optional[str] = None
        self._feedback_timer = 0.0

        self._title_font = pygame.font.SysFont("arial", 24, bold=True)
        self._item_font = pygame.font.SysFont("arial", 18)
        self._hint_font = pygame.font.SysFont("arial", 14)
        self._feedback_font = pygame.font.SysFont("arial", 16, bold=True)

    def _show_feedback(self, message: str, duration: float = 2.0) -> None:
        self._feedback_message = message
        self._feedback_timer = duration

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self._done = True
            return

        items = self.get_items()
        if not items:
            return  # nada que navegar si ya se compró todo

        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected_index = (self.selected_index - 1) % len(items)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected_index = (self.selected_index + 1) % len(items)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.selected_index = min(self.selected_index, len(items) - 1)
            item = items[self.selected_index]
            if item.unlocked:
                self._show_feedback(f"Ya tienes {item.name}")
            elif self.attempt_purchase(item):
                self._show_feedback(f"Comprado: {item.name}")
            else:
                self._show_feedback("No te alcanzan las monedas")

    def update(self, dt: float) -> None:
        if self._feedback_timer > 0:
            self._feedback_timer -= dt
            if self._feedback_timer <= 0:
                self._feedback_message = None

    def is_done(self) -> bool:
        return self._done

    def draw(self, surface: pygame.Surface) -> None:
        overlay_bg = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay_bg.fill((0, 0, 0))
        overlay_bg.set_alpha(180)
        surface.blit(overlay_bg, (0, 0))

        items = self.get_items()
        row_count = max(len(items), 1)
        box_width, box_height = 420, 100 + 30 * row_count
        box = pygame.Rect(0, 0, box_width, box_height)
        box.center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        pygame.draw.rect(surface, (30, 30, 40), box, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 210), box, width=2, border_radius=8)

        title = self._title_font.render(
            f"Tienda — {self.get_balance()} monedas", True, (255, 255, 255)
        )
        surface.blit(title, (box.x + 20, box.y + 16))

        if not items:
            empty_text = self._item_font.render("Ya tienes todo lo disponible.", True, (200, 200, 200))
            surface.blit(empty_text, (box.x + 30, box.y + 60))
        else:
            self.selected_index = min(self.selected_index, len(items) - 1)
            for i, item in enumerate(items):
                y = box.y + 60 + i * 30
                is_selected = i == self.selected_index
                color = (255, 230, 120) if is_selected else (220, 220, 220)
                prefix = "> " if is_selected else "  "
                status = "Adquirido" if item.unlocked else f"{item.price} monedas"
                line = f"{prefix}[{item.kind_label}] {item.name} — {status}"
                text = self._item_font.render(line, True, color)
                surface.blit(text, (box.x + 24, y))

        if self._feedback_message is not None:
            feedback = self._feedback_font.render(self._feedback_message, True, (150, 255, 180))
            surface.blit(feedback, (box.x + 20, box.bottom - 52))

        hint = self._hint_font.render(
            "↑↓ mover · Enter comprar · Esc salir", True, (170, 170, 170)
        )
        surface.blit(hint, (box.x + 20, box.bottom - 26))
# IRONEDIT:1783512345:e03fdc9c6a136cecdda562676ddec07dde0df19a8e0a60f5933007238ec5e815
