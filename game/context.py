"""
RoomContext agrupa las referencias que un Interactable podría necesitar al
activarse (room_manager, economy, unlocks, hud_messages, overlay_host,
level_launcher) en un solo objeto, en vez de que cada Interactable reciba
media docena de parámetros sueltos en su constructor o importe módulos
globales directamente.

Esto mantiene bajo el acoplamiento: un Interactable solo sabe "recibo un
context con estas cosas adentro", lo cual también hace más fácil testear
un Interactable de forma aislada con un context de prueba (mock).

overlay_host y level_launcher son Protocol (interfaces mínimas) en vez de
referencias directas a LobbyState/GameStateManager — así un Interactable
nunca necesita conocer esas clases completas, solo el pedacito que
efectivamente usa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from game.world.room_manager import RoomManager
    from game.progression.economy import Economy
    from game.progression.unlocks import Unlocks
    from game.ui.message_queue import MessageQueue
    from game.ui.overlay import Overlay


class OverlayHost(Protocol):
    def open_overlay(self, overlay: "Overlay") -> None: ...


class LevelLauncher(Protocol):
    def start_exploration(self, function_id: str, algorithm_id: str) -> None: ...


@dataclass
class RoomContext:
    room_manager: "RoomManager"
    economy: "Economy"
    unlocks: "Unlocks"
    hud_messages: "MessageQueue"
    overlay_host: "OverlayHost"
    level_launcher: "LevelLauncher"
# IRONEDIT:1783483891:8b6a6a1d10d4396a1621f639d46deb00842c9a049f207a9dbc432775ef7912a6
