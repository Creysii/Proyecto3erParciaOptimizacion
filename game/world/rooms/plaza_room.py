"""
La plaza principal del lobby: una sola pantalla, con el edificio de la
tienda a un lado y los portales de nivel del otro. Es la primera room
que el jugador ve al entrar al juego.
"""

from __future__ import annotations

import pygame

from game import config
from game.data.terrain_functions_config import TERRAIN_FUNCTIONS
from game.interactables.door_interactable import DoorInteractable
from game.interactables.level_portal_interactable import LevelPortalInteractable
from game.world.room import Room

WALL_THICKNESS = 24

SHOP_BUILDING_RECT = pygame.Rect(60, 220, 160, 100)
# La puerta arranca EXACTAMENTE donde termina la colisión del edificio
# (SHOP_BUILDING_RECT.bottom == 320), para que no se solape con la pared
# y el jugador pueda pisarla sin quedar bloqueado.
SHOP_DOOR_RECT = pygame.Rect(120, SHOP_BUILDING_RECT.bottom, 40, 24)


class PlazaRoom(Room):
    def __init__(self) -> None:
        super().__init__(room_id="plaza", background_color=config.COLOR_BG_PLAZA)

        self._build_boundary_walls()
        self._build_shop_building()
        self._build_level_portals()

        self.spawn_points = {
            "default": (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 100),
            # Justo frente a la puerta de la tienda, para que al salir el
            # jugador reaparezca mirando hacia el edificio, no de espaldas.
            "desde_tienda": (SHOP_DOOR_RECT.centerx, SHOP_DOOR_RECT.bottom + 24),
        }

    def _build_boundary_walls(self) -> None:
        w, h, t = config.SCREEN_WIDTH, config.SCREEN_HEIGHT, WALL_THICKNESS
        walls = [
            pygame.Rect(0, 0, w, t),           # arriba
            pygame.Rect(0, h - t, w, t),        # abajo
            pygame.Rect(0, 0, t, h),            # izquierda
            pygame.Rect(w - t, 0, t, h),        # derecha
        ]
        for wall in walls:
            self.collision_rects.append(wall)
            self.static_visuals.append((wall, config.COLOR_WALL))

    def _build_shop_building(self) -> None:
        # El edificio completo es colisión...
        self.collision_rects.append(SHOP_BUILDING_RECT)
        self.static_visuals.append((SHOP_BUILDING_RECT, config.COLOR_SHOP_BUILDING))

        # ...excepto que la puerta NO debe estar en collision_rects (si no,
        # el jugador nunca podría pisarla para activarla). La dibujamos
        # encima del edificio como zona distinta y la registramos como
        # DoorInteractable en vez de como pared.
        door = DoorInteractable(
            rect=SHOP_DOOR_RECT.copy(),
            target_room_id="tienda",
            target_spawn_id="entrada",
        )
        self.interactables.append(door)

    def _build_level_portals(self) -> None:
        for function_config in TERRAIN_FUNCTIONS:
            self.interactables.append(LevelPortalInteractable(function_config))
# IRONEDIT:1783483892:efcfde8eb472f61e172b26bdbc8fc3605b0532db6ff4141ddc3b62f16937a35c
