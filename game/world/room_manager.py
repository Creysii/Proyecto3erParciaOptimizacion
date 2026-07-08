"""
RoomManager: dueño del grafo de rooms del lobby. Sabe cuál room está
activa, resuelve qué interactable debe dispararse cada frame, y coordina
la transición (fade) cuando el jugador cambia de room.

El cambio real de room NO ocurre en transition_to(): ahí solo se arranca
el fade. El cambio real ocurre en _perform_transition(), que se pasa como
callback a Transition.start() y se ejecuta en el punto más oscuro del
fade — así el jugador nunca ve el cambio de escena a medio construir.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game.transition import Transition

if TYPE_CHECKING:
    from game.context import RoomContext
    from game.entities.player import Player
    from game.world.room import Room


class RoomManager:
    def __init__(
        self,
        rooms: dict[str, "Room"],
        initial_room_id: str,
        initial_spawn_id: str,
        player: "Player",
    ) -> None:
        self.rooms = rooms
        self.player = player
        self.transition = Transition()

        self._pending_room_id: str | None = None
        self._pending_spawn_id: str | None = None

        self.active_room = self.rooms[initial_room_id]
        self.active_room.on_enter(initial_spawn_id)
        self.player.set_position(self.active_room.get_spawn_position(initial_spawn_id))

    # ------------------------------------------------------------------
    # Transición entre rooms
    # ------------------------------------------------------------------
    def transition_to(self, room_id: str, spawn_id: str) -> None:
        if room_id not in self.rooms:
            raise KeyError(f"RoomManager no conoce la room '{room_id}'")
        self._pending_room_id = room_id
        self._pending_spawn_id = spawn_id
        self.transition.start(on_midpoint=self._perform_transition)

    def _perform_transition(self) -> None:
        assert self._pending_room_id is not None
        assert self._pending_spawn_id is not None

        self.active_room.on_exit()
        self.active_room = self.rooms[self._pending_room_id]
        self.active_room.on_enter(self._pending_spawn_id)
        self.player.set_position(self.active_room.get_spawn_position(self._pending_spawn_id))

        self._pending_room_id = None
        self._pending_spawn_id = None

    # ------------------------------------------------------------------
    # Ciclo por frame
    # ------------------------------------------------------------------
    def update(self, dt: float, interact_pressed: bool, context: "RoomContext") -> None:
        self.transition.update(dt)

        # Mientras el fade está en curso, no se procesa movimiento ni
        # interacciones: evita que el jugador siga caminando o dispare
        # un segundo trigger mientras la pantalla está en negro.
        if self.transition.is_active():
            return

        self.active_room.update(dt, self.player)
        self._resolve_interactions(interact_pressed, context)

    def _resolve_interactions(self, interact_pressed: bool, context: "RoomContext") -> None:
        for interactable in self.active_room.interactables:
            if interactable.check_trigger(self.player, interact_pressed, self.active_room.viewport):
                interactable.on_activate(context)
                # Solo un interactable se activa por frame: evita que dos
                # zonas superpuestas (ej. puerta muy pegada a un portal)
                # disparen ambas en el mismo instante.
                break

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, context: "RoomContext") -> None:
        self.active_room.draw(surface, context)
        self.player.draw(surface, self.active_room.viewport)
        self.transition.draw(surface)

    def get_active_prompt(self) -> str | None:
        return self.active_room.find_active_prompt(self.player)
# IRONEDIT:1783483892:1cc026694b3b165f73819e0ba35a92db58d32fcf96cc033590ec7a7b24db600b
