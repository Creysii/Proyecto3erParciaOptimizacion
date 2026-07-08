"""
Tests de comportamiento de ExplorationState — cubren las regresiones
reportadas: cámara fija durante CHOOSING_START (para que el movimiento se
perciba), velocidad consistente con el nivel de zoom, y que los óptimos
globales (incluyendo los múltiples de Himmelblau) se incluyan en el
encuadre panorámico usado tanto por el modo observador como al finalizar
la partida.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from game.session import GameSession
from game.states.exploration_state import ExplorationState
from optimization.level_room import RunPhase


@pytest.fixture(autouse=True, scope="module")
def _pygame_headless():
    pygame.init()
    pygame.display.set_mode((960, 640))
    yield
    pygame.quit()


def _hold_key_and_measure_screen_delta(exploration, key, frames=30, dt=1 / 60):
    p0 = exploration.viewport.domain_to_screen(
        (exploration.player.position.x, exploration.player.position.y)
    )
    fake_keys = {key: True}

    class FakeKeys(dict):
        def __getitem__(self, k):
            return self.get(k, False)

    original = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: FakeKeys(fake_keys)
    for _ in range(frames):
        exploration.update(dt)
    pygame.key.get_pressed = original

    p1 = exploration.viewport.domain_to_screen(
        (exploration.player.position.x, exploration.player.position.y)
    )
    return p1[0] - p0[0]


def test_camera_center_is_fixed_during_choosing_start_regardless_of_player_movement():
    """Regresión: antes, la cámara perseguía al jugador incluso durante
    CHOOSING_START, cancelando casi todo el desplazamiento visible en
    pantalla (movimiento imperceptible). Ahora el centro debe permanecer
    fijo en el centro del dominio mientras el jugador camina libremente."""
    session = GameSession.new_game()
    exploration = ExplorationState("rosenbrock", "hooke_jeeves", session, on_finish=lambda: None)
    assert exploration.run.phase == RunPhase.CHOOSING_START

    (x_min, x_max), (y_min, y_max) = exploration.terrain.bounds
    expected_fixed_center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)

    centers_seen = []
    for _ in range(20):
        exploration.player.position.x += 0.05  # simula desplazamiento real
        exploration.update(1 / 60)
        centers_seen.append(exploration.viewport.state.center)

    for center in centers_seen:
        assert center == pytest.approx(expected_fixed_center, abs=1e-6)


def test_player_movement_is_clearly_perceptible_during_choosing_start():
    session = GameSession.new_game()
    exploration = ExplorationState("rosenbrock", "hooke_jeeves", session, on_finish=lambda: None)
    delta_px = _hold_key_and_measure_screen_delta(exploration, pygame.K_d, frames=30)
    assert delta_px > 40, "El movimiento debería notarse claramente en pantalla"


def test_camera_follows_player_during_showing_candidates():
    """A diferencia de CHOOSING_START, aquí la cámara SÍ debe perseguir
    activamente al jugador (comportamiento ya existente, sin cambios)."""
    session = GameSession.new_game()
    exploration = ExplorationState("rosenbrock", "hooke_jeeves", session, on_finish=lambda: None)
    exploration.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    for _ in range(60):
        exploration.update(1 / 60)

    centers = []
    for _ in range(15):
        exploration.player.position.x += 0.01
        exploration.update(1 / 60)
        centers.append(exploration.viewport.state.center)

    assert len(set(centers)) > 5  # el centro cambió repetidamente, siguiendo al jugador


def test_speed_scales_with_current_span():
    """Dos escenarios con spans muy distintos (mismo modo de cámara
    activa) deben producir desplazamientos en pantalla del MISMO orden de
    magnitud, no proporcionales a la razón de spans — esa es la propiedad
    de 'velocidad consistente con el zoom'."""
    session_a = GameSession.new_game()
    exp_a = ExplorationState("rosenbrock", "hooke_jeeves", session_a, on_finish=lambda: None)
    exp_a.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    for _ in range(90):
        exp_a.update(1 / 60)
    span_a = exp_a.viewport.state.span
    delta_a = _hold_key_and_measure_screen_delta(exp_a, pygame.K_d, frames=30)

    session_b = GameSession.new_game()
    exp_b = ExplorationState("sphere", "newton", session_b, on_finish=lambda: None)
    exp_b.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    for _ in range(3):
        best = min(exp_b.run.current_candidates, key=lambda c: c.f_value)
        exp_b.player.set_position(best.position)
        exp_b.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        for _ in range(30):
            exp_b.update(1 / 60)
    span_b = exp_b.viewport.state.span
    delta_b = _hold_key_and_measure_screen_delta(exp_b, pygame.K_d, frames=30)

    span_ratio = span_a / span_b
    displacement_ratio = delta_a / max(delta_b, 0.001)

    assert span_ratio > 20  # los spans son MUY distintos
    # pero el desplazamiento en pantalla debe quedarse en un orden de
    # magnitud razonable (no reproducir la misma razón de 20x+)
    assert displacement_ratio < 5.0


def test_overview_target_includes_all_of_himmelblau_optima():
    """Himmelblau tiene 4 óptimos globales — el encuadre panorámico (usado
    tanto por el modo K como al finalizar la partida) debe incluirlos
    TODOS, no solo el representativo, para que el marcador nunca quede
    fuera de pantalla sin importar a cuál convergió el jugador."""
    session = GameSession.new_game()
    exploration = ExplorationState("himmelblau", "newton", session, on_finish=lambda: None)

    target = exploration._compute_overview_target()

    all_optima = [
        exploration.terrain.global_optimum_position,
        *exploration.terrain.additional_global_optima,
    ]
    assert len(all_optima) == 4

    half_span = target.span / 2.0
    for ox, oy in all_optima:
        assert abs(ox - target.center[0]) <= half_span + 1e-6
        assert abs(oy - target.center[1]) <= half_span + 1e-6


def test_finish_sequence_keeps_moving_camera_toward_overview():
    """Regresión: antes, al finalizar la corrida, update() retornaba
    temprano sin volver a tocar la cámara — si el algoritmo convergió
    lejos del óptimo real, el marcador podía quedar fuera de pantalla
    para siempre durante la pantalla de resultado."""
    session = GameSession.new_game()
    exploration = ExplorationState("rastrigin", "newton", session, on_finish=lambda: None)
    exploration.player.set_position((3.5, -2.7))
    exploration.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    for _ in range(20):
        if exploration.run.is_finished():
            break
        best = min(exploration.run.current_candidates, key=lambda c: c.f_value)
        exploration.player.set_position(best.position)
        exploration.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        exploration.update(1 / 60)
    if not exploration.run.is_finished():
        exploration.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v))

    assert exploration._finish_timer is not None
    span_right_after_finish = exploration.viewport.state.span

    for _ in range(90):
        exploration.update(1 / 60)

    span_later = exploration.viewport.state.span
    assert span_later != pytest.approx(span_right_after_finish), (
        "La cámara debería seguir moviéndose tras finalizar, no quedar congelada"
    )

    marker_screen = exploration.viewport.domain_to_screen(exploration.terrain.global_optimum_position)
    final_screen = exploration.viewport.domain_to_screen(exploration.run.result.x_final)
    assert exploration.playable_rect.collidepoint(marker_screen)
    assert exploration.playable_rect.collidepoint(final_screen)
# IRONEDIT:1783512345:ac9c9f9160eb998d7fdf32b103a56ba1aecd9f51702b713ee4d2ad01985002ca
