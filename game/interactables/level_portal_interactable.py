"""
Portal hacia una función objetivo. Si la función está desbloqueada, abre
DetectorSelectMenu para que el jugador elija con qué algoritmo explorarla.
Si está bloqueada, muestra un mensaje con el costo de desbloqueo, sin
transicionar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game import config
from game.data.terrain_functions_config import TerrainFunctionConfig
from game.interactables.base_interactable import Interactable, TriggerMode
from game.ui.detector_select_menu import DetectorSelectMenu

if TYPE_CHECKING:
    from game.context import RoomContext

PORTAL_RADIUS = 26


class LevelPortalInteractable(Interactable):
    def __init__(self, function_config: TerrainFunctionConfig) -> None:
        cx, cy = function_config.portal_position
        rect = pygame.Rect(0, 0, PORTAL_RADIUS * 2, PORTAL_RADIUS * 2)
        rect.center = (cx, cy)
        super().__init__(rect, trigger_mode=TriggerMode.ON_OVERLAP, prompt_text=function_config.name)
        self.function_config = function_config

    def on_activate(self, context: "RoomContext") -> None:
        if not context.unlocks.is_function_unlocked(self.function_config.id):
            context.hud_messages.show(self._locked_message())
            return

        unlocked_algorithms = context.unlocks.get_unlocked_algorithm_ids()
        context.overlay_host.open_overlay(
            DetectorSelectMenu(
                function_id=self.function_config.id,
                function_name=self.function_config.name,
                unlocked_algorithm_ids=unlocked_algorithms,
                on_select=lambda algo_id: context.level_launcher.start_exploration(
                    self.function_config.id, algo_id
                ),
            )
        )

    def _locked_message(self) -> str:
        cfg = self.function_config
        return f"{cfg.name} bloqueado — necesitas {cfg.unlock_cost_coins} monedas"

    def draw_indicator(self, surface: pygame.Surface, context: "RoomContext") -> None:
        center = self.rect.center
        unlocked = context.unlocks.is_function_unlocked(self.function_config.id)
        color = config.COLOR_PORTAL_UNLOCKED if unlocked else config.COLOR_PORTAL_LOCKED
        pygame.draw.circle(surface, color, center, PORTAL_RADIUS)
        pygame.draw.circle(surface, (0, 0, 0), center, PORTAL_RADIUS, width=2)

        if not unlocked:
            self._draw_lock_icon(surface, center)

    def _draw_lock_icon(self, surface: pygame.Surface, center: tuple[int, int]) -> None:
        cx, cy = center
        body = pygame.Rect(0, 0, 16, 12)
        body.center = (cx, cy + 4)
        pygame.draw.rect(surface, config.COLOR_LOCK_ICON, body, border_radius=2)
        shackle_rect = pygame.Rect(0, 0, 12, 12)
        shackle_rect.center = (cx, cy - 4)
        pygame.draw.arc(
            surface,
            config.COLOR_LOCK_ICON,
            shackle_rect,
            0.0,
            3.14159,
            width=3,
        )
# IRONEDIT:1783483891:7fdcbdeb6d2ad5dfaabad4a304ec91207e649ed0c66c3647114c708f9a4022b4
