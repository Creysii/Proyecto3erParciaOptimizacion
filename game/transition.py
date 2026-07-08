"""
Transición de fade a negro, reutilizable para cualquier cambio de escena.

Deliberadamente no sabe nada de rooms, jugador ni estados de juego: solo
sube y baja el alpha de un rectángulo negro de pantalla completa, y en el
punto más oscuro (mitad del proceso) dispara un callback. Quien la usa
(RoomManager, y a futuro cualquier cambio de state) decide qué hacer en
ese punto ciego.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

import pygame

from game import config


class TransitionState(Enum):
    IDLE = auto()
    FADING_OUT = auto()
    FADING_IN = auto()


class Transition:
    def __init__(
        self,
        duration_out: float = config.TRANSITION_FADE_OUT,
        duration_in: float = config.TRANSITION_FADE_IN,
    ) -> None:
        self._duration_out = duration_out
        self._duration_in = duration_in

        self.state: TransitionState = TransitionState.IDLE
        self._timer: float = 0.0
        self._on_midpoint: Optional[Callable[[], None]] = None
        self._midpoint_fired: bool = False

        self._overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self._overlay.fill((0, 0, 0))

    def is_active(self) -> bool:
        return self.state != TransitionState.IDLE

    def start(self, on_midpoint: Callable[[], None]) -> None:
        """Inicia una transición. Si ya hay una en curso, la ignora (evita
        que dos transiciones se pisen si el jugador dispara dos triggers
        casi al mismo tiempo)."""
        if self.is_active():
            return
        self._on_midpoint = on_midpoint
        self._midpoint_fired = False
        self._timer = 0.0
        self.state = TransitionState.FADING_OUT

    def update(self, dt: float) -> None:
        if self.state == TransitionState.IDLE:
            return

        self._timer += dt

        if self.state == TransitionState.FADING_OUT:
            if self._timer >= self._duration_out:
                # Punto más oscuro: aquí se dispara el cambio real de room.
                if not self._midpoint_fired and self._on_midpoint is not None:
                    self._on_midpoint()
                    self._midpoint_fired = True
                self.state = TransitionState.FADING_IN
                self._timer = 0.0

        elif self.state == TransitionState.FADING_IN:
            if self._timer >= self._duration_in:
                self.state = TransitionState.IDLE
                self._timer = 0.0
                self._on_midpoint = None

    def _current_alpha(self) -> int:
        if self.state == TransitionState.FADING_OUT:
            progress = min(self._timer / self._duration_out, 1.0)
            return int(255 * progress)
        if self.state == TransitionState.FADING_IN:
            progress = min(self._timer / self._duration_in, 1.0)
            return int(255 * (1.0 - progress))
        return 0

    def draw(self, surface: pygame.Surface) -> None:
        if self.state == TransitionState.IDLE:
            return
        self._overlay.set_alpha(self._current_alpha())
        surface.blit(self._overlay, (0, 0))
# IRONEDIT:1783483891:73fd15a6fe1e7b623e9fc1efd1d1a5fa78b8a77e67b501a4aa509bb8cb85022e
