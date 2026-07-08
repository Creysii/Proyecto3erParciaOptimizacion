"""
Interior de la tienda. Ahora incluye un vendedor real (ShopVendorInteractable)
que abre la interfaz de compra al presionar E — el contenedor navegable ya
existía desde antes; añadir el vendedor fue exactamente agregar un ítem más
a self.interactables, sin tocar nada de la colisión ni de las puertas.
"""

from __future__ import annotations

import pygame

from game import config
from game.interactables.door_interactable import DoorInteractable
from game.interactables.shop_vendor_interactable import ShopVendorInteractable
from game.world.room import Room

WALL_THICKNESS = 24
ROOM_WIDTH = 360
ROOM_HEIGHT = 260

# La tienda es un espacio más chico, centrado en la pantalla, para que se
# sienta como un interior distinto y no como "la plaza pero de otro color".
ROOM_OFFSET_X = (config.SCREEN_WIDTH - ROOM_WIDTH) // 2
ROOM_OFFSET_Y = (config.SCREEN_HEIGHT - ROOM_HEIGHT) // 2

EXIT_DOOR_RECT = pygame.Rect(
    ROOM_OFFSET_X + ROOM_WIDTH // 2 - 20,
    ROOM_OFFSET_Y - WALL_THICKNESS,
    40,
    WALL_THICKNESS,
)

VENDOR_POSITION = (config.SCREEN_WIDTH // 2, ROOM_OFFSET_Y + 70)


class ShopRoom(Room):
    def __init__(self) -> None:
        super().__init__(room_id="tienda", background_color=config.COLOR_BG_SHOP)

        self._build_walls()
        self._build_exit_door()
        self._build_vendor()

        self.spawn_points = {
            "entrada": (config.SCREEN_WIDTH // 2, ROOM_OFFSET_Y + ROOM_HEIGHT - 60),
        }

    def _build_walls(self) -> None:
        outer = pygame.Rect(
            ROOM_OFFSET_X - WALL_THICKNESS,
            ROOM_OFFSET_Y - WALL_THICKNESS,
            ROOM_WIDTH + WALL_THICKNESS * 2,
            ROOM_HEIGHT + WALL_THICKNESS * 2,
        )
        inner = pygame.Rect(ROOM_OFFSET_X, ROOM_OFFSET_Y, ROOM_WIDTH, ROOM_HEIGHT)

        # El muro superior se parte en dos segmentos, dejando un hueco
        # exacto del ancho de EXIT_DOOR_RECT — si fuera una sola franja
        # continua, su colisión taparía la puerta y el jugador nunca
        # podría pisarla (mismo error que se corrigió en PlazaRoom).
        top_left = pygame.Rect(
            outer.left, outer.top, EXIT_DOOR_RECT.left - outer.left, WALL_THICKNESS
        )
        top_right = pygame.Rect(
            EXIT_DOOR_RECT.right,
            outer.top,
            outer.right - EXIT_DOOR_RECT.right,
            WALL_THICKNESS,
        )
        bottom = pygame.Rect(outer.left, inner.bottom, outer.width, WALL_THICKNESS)
        left = pygame.Rect(outer.left, outer.top, WALL_THICKNESS, outer.height)
        right = pygame.Rect(inner.right, outer.top, WALL_THICKNESS, outer.height)

        for wall in (top_left, top_right, bottom, left, right):
            self.collision_rects.append(wall)
            self.static_visuals.append((wall, config.COLOR_WALL))

    def _build_exit_door(self) -> None:
        # La puerta de salida vive exactamente en el hueco dejado entre
        # top_left y top_right en _build_walls.
        door = DoorInteractable(
            rect=EXIT_DOOR_RECT.copy(),
            target_room_id="plaza",
            target_spawn_id="desde_tienda",
        )
        self.interactables.append(door)

    def _build_vendor(self) -> None:
        # ON_INTERACT (requiere E, no solo pisarlo) — hablar con el
        # vendedor nunca debe ser accidental, a diferencia de las puertas.
        self.interactables.append(ShopVendorInteractable(VENDOR_POSITION))
# IRONEDIT:1783512345:bb65bda3a24db20f9ddc4bc7c4c520604c978eb4eec19869e13282c56a2720fa
