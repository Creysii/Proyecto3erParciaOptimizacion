"""
Clase base para cualquier espacio caminable: la plaza del lobby, el
interior de la tienda, y a futuro cualquier antesala de nivel.

Deliberadamente NO conoce Economy/Unlocks/RoomManager directamente — todo
lo que un Interactable dentro de la room necesite de esos sistemas llega
a través del RoomContext en el momento de la activación, no antes.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional

import pygame

from game.world.viewport import IdentityViewport, Viewport

if TYPE_CHECKING:
    from game.context import RoomContext
    from game.entities.player import Player
    from game.interactables.base_interactable import Interactable


class Room(ABC):
    def __init__(self, room_id: str, background_color: tuple[int, int, int]) -> None:
        self.room_id = room_id
        self.background_color = background_color

        self.collision_rects: list[pygame.Rect] = []
        self.interactables: list["Interactable"] = []
        self.spawn_points: dict[str, tuple[int, int]] = {}

        # Elementos puramente visuales (paredes, el edificio de la tienda).
        # Separado de collision_rects porque no todo lo visual es colisión
        # (a futuro: alfombras, sombras) ni toda colisión necesita un color
        # propio (algunos interactables ya se dibujan solos vía draw_indicator).
        self.static_visuals: list[tuple[pygame.Rect, tuple[int, int, int]]] = []

        # Todas las rooms del lobby (Plaza/Shop) usan 1:1 sin transformación
        # — este atributo formaliza lo que antes era implícito, y es el
        # punto de extensión que usaría cualquier Room futura que necesite
        # zoom dinámico (aunque, en la práctica, la exploración real vive
        # en ExplorationState, fuera de RoomManager, con su propio
        # DecisionViewport independiente de este atributo).
        self.viewport: Viewport = IdentityViewport()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def on_enter(self, spawn_id: str) -> None:
        """Se llama cuando la room se vuelve activa. Por defecto no hace
        nada extra; subclases pueden sobreescribir para reiniciar estado
        (ej. reactivar NPCs, resetear animaciones ambientales)."""
        return

    def on_exit(self) -> None:
        """Se llama justo antes de dejar de ser la room activa. Hook para
        pausar timers o sonidos ambientales específicos de esta room."""
        return

    # ------------------------------------------------------------------
    # Ciclo por frame
    # ------------------------------------------------------------------
    def update(self, dt: float, player: "Player") -> None:
        """Comportamiento genérico compartido por todas las rooms: mover
        al jugador contra la colisión propia de esta room. Las subclases
        no necesitan sobreescribir esto — su diferencia es de contenido
        (qué collision_rects e interactables tienen), no de comportamiento."""
        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.try_move(dt, self.collision_rects, self.viewport)

    def draw(self, surface: pygame.Surface, context: "RoomContext") -> None:
        surface.fill(self.background_color)
        for rect, color in self.static_visuals:
            pygame.draw.rect(surface, color, rect)
        for interactable in self.interactables:
            interactable.draw_indicator(surface, context)

    # ------------------------------------------------------------------
    # Spawns
    # ------------------------------------------------------------------
    def get_spawn_position(self, spawn_id: str) -> tuple[int, int]:
        if spawn_id not in self.spawn_points:
            raise KeyError(
                f"Room '{self.room_id}' no tiene spawn_point '{spawn_id}'. "
                f"Disponibles: {list(self.spawn_points.keys())}"
            )
        return self.spawn_points[spawn_id]

    def find_active_prompt(self, player: "Player") -> Optional[str]:
        """Devuelve el prompt_text del primer interactable ON_INTERACT en
        rango del jugador, o None. Usado por la UI para mostrar '[E] hablar'
        solo cuando corresponde."""
        from game.interactables.base_interactable import TriggerMode  # import local: evita ciclo

        for interactable in self.interactables:
            if (
                interactable.trigger_mode == TriggerMode.ON_INTERACT
                and interactable.prompt_text is not None
                and interactable.is_player_in_range(player, self.viewport)
            ):
                return interactable.prompt_text
        return None
# IRONEDIT:1783483892:262166deaf4441b4a85135c691b0d46b1f6d7a76712c76b3e740558aa384cbc2
