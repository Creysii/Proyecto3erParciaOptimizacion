"""
Interior de la tienda. Por ahora está vacía a propósito (sin vendedor, sin
inventario) — esta entrega solo construye el contenedor navegable completo:
la habitación, su colisión, y la puerta que regresa a la plaza. Cuando se
añada ShopVendorInteractable más adelante, es agregar un item más a
self.interactables; nada de esto necesita cambiar.
"""

from __future__ import annotations

import pygame

from game import config
from game.interactables.door_interactable import DoorInteractable
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


class ShopRoom(Room):
    def __init__(self) -> None:
        super().__init__(room_id="tienda", background_color=config.COLOR_BG_SHOP)

        self._build_walls()
        self._build_exit_door()
        self._build_placeholder_sign()

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

    def _build_placeholder_sign(self) -> None:
        # Marca puramente visual (no colisión, no interactable) para dejar
        # claro que la vacuidad es intencional y no un bug de renderizado.
        sign_rect = pygame.Rect(0, 0, 200, 40)
        sign_rect.center = (config.SCREEN_WIDTH // 2, ROOM_OFFSET_Y + 60)
        self.static_visuals.append((sign_rect, (40, 34, 28)))
        self._sign_rect = sign_rect

    def draw(self, surface: pygame.Surface, context) -> None:  # type: ignore[override]
        super().draw(surface, context)
        font = pygame.font.SysFont("arial", 18, bold=True)
        text = font.render("Próximamente", True, (230, 220, 200))
        text_rect = text.get_rect(center=self._sign_rect.center)
        surface.blit(text, text_rect)
# IRONEDIT:1783483892:1ae1d80b4ee4dd5fc81feebd577e0e4ef4861fbfb3c81a0085e7d18016abb285
