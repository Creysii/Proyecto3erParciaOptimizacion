"""
LobbyState: el "pegamento" que arma todo lo del lobby. Ya NO crea su
propia Economy/Unlocks — las recibe de GameSession (dueño único,
compartido con ExplorationState). Implementa OverlayHost para que los
Interactables puedan pedirle que abra un overlay (DetectorSelectMenu hoy,
el overlay de tienda más adelante) sin conocer LobbyState por completo.
"""

from __future__ import annotations

from typing import Optional

import pygame

from game.context import RoomContext
from game.entities.player import Player
from game.session import GameSession
from game.ui.hud import HUD
from game.ui.message_queue import MessageQueue
from game.ui.overlay import Overlay
from game.world.room_manager import RoomManager
from game.world.rooms.plaza_room import PlazaRoom
from game.world.rooms.shop_room import ShopRoom


class LobbyState:
    def __init__(self, session: GameSession, level_launcher) -> None:
        self.session = session
        self.hud_messages = MessageQueue()

        self.player = Player(start_pos=(0, 0))  # posición real la fija RoomManager

        rooms = {
            "plaza": PlazaRoom(),
            "tienda": ShopRoom(),
        }
        self.room_manager = RoomManager(
            rooms=rooms,
            initial_room_id="plaza",
            initial_spawn_id="default",
            player=self.player,
        )

        self.context = RoomContext(
            room_manager=self.room_manager,
            economy=session.economy,
            unlocks=session.unlocks,
            hud_messages=self.hud_messages,
            overlay_host=self,
            level_launcher=level_launcher,
        )

        self.hud = HUD(session.economy)

        self.active_overlay: Optional[Overlay] = None
        self._interact_pressed_this_frame = False

    # ------------------------------------------------------------------
    # OverlayHost
    # ------------------------------------------------------------------
    def open_overlay(self, overlay: Overlay) -> None:
        self.active_overlay = overlay

    # ------------------------------------------------------------------
    def on_resume(self) -> None:
        """Se llama cuando GameStateManager vuelve a mostrar el lobby
        tras una corrida de exploración. Por ahora no necesita hacer
        nada especial, pero es el punto de extensión correcto si en el
        futuro hiciera falta (ej. refrescar visualmente el estado de
        portales que se acaban de desbloquear)."""
        return

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.active_overlay is not None:
            self.active_overlay.handle_event(event)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self._interact_pressed_this_frame = True

    def update(self, dt: float) -> None:
        if self.active_overlay is not None:
            self.active_overlay.update(dt)
            if self.active_overlay.is_done():
                self.active_overlay = None
            return

        self.room_manager.update(dt, self._interact_pressed_this_frame, self.context)
        self.hud_messages.update(dt)
        self._interact_pressed_this_frame = False

    def draw(self, surface: pygame.Surface) -> None:
        self.room_manager.draw(surface, self.context)
        self.hud.draw(surface, self.room_manager.get_active_prompt())
        self.hud_messages.draw(surface)
        if self.active_overlay is not None:
            self.active_overlay.draw(surface)
# IRONEDIT:1783483891:adeba09ffc1c788021d2c521d0672b8ad31c9ca4938cc924cab40ac33e82e8ea
