"""
Puerta entre dos rooms. Al pisarla, dispara la transición del RoomManager
hacia la room y spawn_point de destino. La puerta de la tienda en la plaza
y la puerta de salida dentro de la tienda son ambas instancias de esta
clase, apuntando una hacia la otra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game import config
from game.interactables.base_interactable import Interactable, TriggerMode

if TYPE_CHECKING:
    from game.context import RoomContext


class DoorInteractable(Interactable):
    def __init__(
        self,
        rect: pygame.Rect,
        target_room_id: str,
        target_spawn_id: str,
    ) -> None:
        super().__init__(rect, trigger_mode=TriggerMode.ON_OVERLAP)
        self.target_room_id = target_room_id
        self.target_spawn_id = target_spawn_id

    def on_activate(self, context: "RoomContext") -> None:
        context.room_manager.transition_to(self.target_room_id, self.target_spawn_id)

    def draw_indicator(self, surface: pygame.Surface, context: "RoomContext") -> None:
        pygame.draw.rect(surface, config.COLOR_DOOR, self.rect, border_radius=3)
# IRONEDIT:1783483891:b81eae5ab7ddfa736ad403c05d1800b303b17c8105a96a3ff698e30c100adb9d
