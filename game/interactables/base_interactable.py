"""
Interactable: cualquier zona de la room con la que el jugador puede
"hacer algo" — puertas, portales de nivel, y a futuro NPCs o cofres.

Dos modos de disparo:
  - ON_OVERLAP: se activa automáticamente al pisar la zona (puertas, portales).
  - ON_INTERACT: requiere que el jugador esté encima Y presione una tecla
    de interacción (NPCs, para evitar activaciones accidentales).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    # Import solo para type checking: evita import circular en runtime,
    # ya que RoomContext termina referenciando cosas que a su vez podrían
    # importar interactables.
    from game.context import RoomContext
    from game.entities.player import Player
    from game.world.viewport import Viewport


class TriggerMode(Enum):
    ON_OVERLAP = auto()
    ON_INTERACT = auto()


class Interactable(ABC):
    def __init__(
        self,
        rect: pygame.Rect,
        trigger_mode: TriggerMode,
        prompt_text: Optional[str] = None,
    ) -> None:
        self.rect = rect
        self.trigger_mode = trigger_mode
        self.prompt_text = prompt_text

    def check_trigger(
        self, player: "Player", interact_pressed: bool, viewport: "Viewport"
    ) -> bool:
        """Decide si este interactable debe activarse este frame."""
        overlapping = self.rect.colliderect(player.get_hitbox(viewport))
        if not overlapping:
            return False

        if self.trigger_mode == TriggerMode.ON_OVERLAP:
            return True
        # ON_INTERACT: solo si además se presionó la tecla de interacción.
        return interact_pressed

    def is_player_in_range(self, player: "Player", viewport: "Viewport") -> bool:
        """Usado para decidir si mostrar el prompt_text, independiente
        de si la tecla fue presionada o no este frame."""
        return self.rect.colliderect(player.get_hitbox(viewport))

    @abstractmethod
    def on_activate(self, context: "RoomContext") -> None:
        """Qué ocurre cuando el interactable se dispara."""
        raise NotImplementedError

    def draw_indicator(self, surface: pygame.Surface, context: "RoomContext") -> None:
        """Hook opcional para dibujar algo distintivo (candado, brillo, etc.).
        Recibe el context porque algunos indicadores dependen de estado en
        vivo (ej. si un portal sigue bloqueado) que puede cambiar a mitad
        de partida. Las subclases sobreescriben si lo necesitan; por defecto
        no dibuja nada más allá de lo que la Room ya dibuje como fondo."""
        return
# IRONEDIT:1783483891:07b7b5b004ee0840cfac6eb666d5b4550e13468c8cd35237049fb4f00eb36342
