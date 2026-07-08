"""
Punto de entrada. Deliberadamente delgado: init de pygame, loop principal,
y todo lo demás vive en GameStateManager y sus dependencias.
"""

from __future__ import annotations

import sys

import pygame

from game import config
from game.session import GameSession
from game.state_manager import GameStateManager


def main() -> None:
    pygame.init()
    pygame.display.set_caption(config.WINDOW_TITLE)
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    session = GameSession.new_game()
    game_state_manager = GameStateManager(session)

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0  # delta time en segundos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                # ESC ya NO se intercepta aquí globalmente — antes esto
                # cerraba el juego completo incluso cuando ESC se
                # presionaba para cancelar un menú (ej. DetectorSelectMenu),
                # porque el evento nunca llegaba a game_state_manager. Cada
                # estado decide localmente qué hacer con ESC (cancelar un
                # overlay, o no hacer nada si no aplica); la única forma
                # de cerrar la ventana ahora es el botón de cerrar del SO
                # (que dispara pygame.QUIT, manejado arriba).
                game_state_manager.handle_event(event)

        game_state_manager.update(dt)
        game_state_manager.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
# IRONEDIT:1783512345:6647b7269e87bca502cd5cdaf2d28b2a5f622e399c19140bc4cf4faca2278bb9
