"""
Verifica que la corrección de colisión de Player.try_move() sea exacta
(sub-píxel) tanto en el caso 1:1 del lobby (IdentityViewport) como bajo
zoom (DecisionViewport) — migra las comprobaciones ad-hoc que se hicieron
por bash durante el desarrollo del lobby a la suite de tests oficial.
"""

from __future__ import annotations

import pygame
import pytest

from game.entities.player import Player
from game.world.viewport import DecisionViewport, IdentityViewport, ViewportState


@pytest.fixture(autouse=True, scope="module")
def _pygame_headless():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield
    pygame.quit()


def test_collision_stops_exactly_at_wall_with_identity_viewport():
    viewport = IdentityViewport()
    wall = pygame.Rect(100, 0, 20, 200)  # pared vertical en x=100..120

    player = Player(start_pos=(50, 50))
    player.velocity = pygame.Vector2(300, 0)  # empujando a la derecha

    for _ in range(60):
        player.try_move(1 / 60, [wall], viewport)

    hitbox = player.get_hitbox(viewport)
    assert hitbox.right == wall.left  # exacto, sin hueco ni penetración


def test_collision_stops_exactly_at_wall_with_decision_viewport_zoomed_in():
    """Mismo test, pero con un DecisionViewport haciendo zoom (span pequeño,
    escala muy distinta de 1:1) — la corrección debe seguir siendo exacta
    porque se calcula vía la conversión real del viewport, no asumiendo
    ninguna escala fija."""
    rect = pygame.Rect(0, 0, 600, 600)
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)
    # Zoom fuerte: span de solo 0.02 unidades de dominio cubriendo 600px.
    viewport.apply_state(ViewportState(center=(0.0, 0.0), span=0.02))

    wall = pygame.Rect(400, 0, 20, 600)  # pared vertical en pantalla

    player = Player(start_pos=(-0.005, 0.0))  # posición en coords de DOMINIO
    player.speed = 0.05  # velocidad pequeña, coherente con el span diminuto
    player.velocity = pygame.Vector2(player.speed, 0)

    for _ in range(200):
        player.try_move(1 / 60, [wall], viewport)

    hitbox = player.get_hitbox(viewport)
    assert hitbox.right == pytest.approx(wall.left, abs=1)


def test_player_never_passes_through_wall_regardless_of_starting_offset():
    """Prueba de robustez: sin importar el offset inicial (siempre que no
    nazca ya solapado), el jugador nunca debe terminar con su hitbox
    penetrando la pared."""
    viewport = IdentityViewport()
    wall = pygame.Rect(200, 0, 20, 200)

    for start_x in [50, 100, 150, 190]:
        player = Player(start_pos=(start_x, 50))
        player.velocity = pygame.Vector2(300, 0)
        for _ in range(60):
            player.try_move(1 / 60, [wall], viewport)
        hitbox = player.get_hitbox(viewport)
        assert hitbox.right <= wall.left, f"Penetró la pared desde start_x={start_x}"


def test_up_intent_moves_player_up_on_screen_with_identity_viewport():
    """Regresión: 'intención de subir' (velocity.y negativo, como genera
    Player.handle_input al presionar W) debe reducir la coordenada Y de
    PANTALLA — el jugador debe verse más arriba, sin importar el viewport."""
    viewport = IdentityViewport()
    player = Player(start_pos=(100.0, 100.0))
    screen_before = viewport.domain_to_screen((player.position.x, player.position.y))

    player.velocity = pygame.Vector2(0, -50)  # intención de subir (como W)
    player.try_move(1 / 60, [], viewport)

    screen_after = viewport.domain_to_screen((player.position.x, player.position.y))
    assert screen_after[1] < screen_before[1], "Debería verse más arriba en pantalla"


def test_up_intent_moves_player_up_on_screen_with_decision_viewport():
    """Mismo test que el anterior, pero con DecisionViewport — el bug real
    reportado: antes de la corrección, 'intención de subir' aquí producía
    el efecto CONTRARIO (el jugador bajaba en pantalla), porque
    domain_to_screen invierte el eje Y para lectura matemática convencional
    y try_move() no compensaba ese signo al integrar la posición."""
    rect = pygame.Rect(0, 0, 600, 600)
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)
    viewport.apply_state(ViewportState(center=(0.0, 0.0), span=10.0))

    player = Player(start_pos=(0.0, 0.0))  # coordenadas de DOMINIO
    screen_before = viewport.domain_to_screen((player.position.x, player.position.y))

    player.velocity = pygame.Vector2(0, -1.0)  # misma intención de subir (como W)
    player.try_move(1 / 60, [], viewport)

    screen_after = viewport.domain_to_screen((player.position.x, player.position.y))
    assert screen_after[1] < screen_before[1], (
        "Debería verse más arriba en pantalla — si esto falla, W está "
        "invertida dentro de una corrida de exploración"
    )
# IRONEDIT:1783483892:9b4c4687a2870b4ecdb6e11b1063ad8fa48d32aee8a0fd8e99d2c6b5c9bdc508
