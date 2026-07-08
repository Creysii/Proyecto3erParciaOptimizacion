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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                game_state_manager.handle_event(event)

        game_state_manager.update(dt)
        game_state_manager.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
