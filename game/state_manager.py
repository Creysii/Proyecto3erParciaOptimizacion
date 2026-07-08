"""
GameStateManager: el objeto de más alto nivel del juego. Mantiene una
única instancia PERSISTENTE de LobbyState (nunca se destruye ni se
reconstruye — el jugador conserva su posición y room activa dentro del
lobby entre corridas), y crea una instancia NUEVA de ExplorationState
cada vez que el jugador entra a una función.
"""

from __future__ import annotations

import pygame

from game.session import GameSession


class GameStateManager:
    def __init__(self, session: GameSession) -> None:
        self.session = session

        # Import diferido para evitar un ciclo de importación:
        # LobbyState necesita conocer el tipo de level_launcher (este
        # objeto), y este objeto necesita construir LobbyState.
        from game.states.lobby_state import LobbyState

        self._lobby_state = LobbyState(session, level_launcher=self)
        self.current_state = self._lobby_state

    def start_exploration(self, function_id: str, algorithm_id: str) -> None:
        from game.states.exploration_state import ExplorationState

        self.current_state = ExplorationState(
            function_id=function_id,
            algorithm_id=algorithm_id,
            session=self.session,
            on_finish=self.return_to_lobby,
        )

    def return_to_lobby(self) -> None:
        self._lobby_state.on_resume()
        self.current_state = self._lobby_state

    def handle_event(self, event: pygame.event.Event) -> None:
        self.current_state.handle_event(event)

    def update(self, dt: float) -> None:
        self.current_state.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.current_state.draw(surface)
# IRONEDIT:1783483891:093f9d8a68aa8661d6733bf25e6a1a369cb44cfab1bfa024b33ea5771e9cbd49
