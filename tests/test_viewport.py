"""
DecisionViewport y CameraFollow son geometría pura — no dependen de una
ventana de pygame abierta (pygame.Rect no requiere display), así que se
testean igual de aislados que el núcleo matemático.
"""

from __future__ import annotations

import inspect

import pygame
import pytest

from game.world.camera_follow import CameraFollow
from game.world.viewport import DecisionViewport, IdentityViewport, ViewportState


def test_identity_viewport_passes_through_unchanged():
    viewport = IdentityViewport()
    assert viewport.domain_to_screen((123.0, 456.0)) == (123, 456)
    assert viewport.screen_to_domain((123, 456)) == (123.0, 456.0)


def test_decision_viewport_domain_to_screen_round_trip():
    rect = pygame.Rect(100, 50, 600, 600)
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)
    viewport.apply_state(ViewportState(center=(1.5, -2.0), span=8.0))

    original = (2.3, -1.1)
    screen_pos = viewport.domain_to_screen(original)
    recovered = viewport.screen_to_domain(screen_pos)

    assert recovered[0] == pytest.approx(original[0], abs=0.05)
    assert recovered[1] == pytest.approx(original[1], abs=0.05)


def test_decision_viewport_y_axis_is_inverted_for_conventional_reading():
    """Un punto con y > centro debe dibujarse MÁS ARRIBA en pantalla
    (coordenada de pantalla menor), como en una gráfica matemática normal."""
    rect = pygame.Rect(0, 0, 600, 600)
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)
    viewport.apply_state(ViewportState(center=(0.0, 0.0), span=10.0))

    screen_above = viewport.domain_to_screen((0.0, 2.0))
    screen_below = viewport.domain_to_screen((0.0, -2.0))
    assert screen_above[1] < screen_below[1]


# ----------------------------------------------------------------------
# compute_target_span: la pieza rediseñada tras el reporte de zoom
# incorrecto. Cubre: (1) la garantía estructural de que la posición del
# jugador no puede colarse en el cálculo, (2) la fórmula geométrica real
# (centroide -> radio máximo -> diámetro -> margen), (3) los casos límite.
# ----------------------------------------------------------------------

def test_compute_target_span_signature_has_no_player_parameter():
    """Verificación estructural (no solo de comportamiento): la firma de
    compute_target_span ni siquiera tiene un parámetro por donde pasar la
    posición del jugador — es la garantía de que este bug no puede
    reintroducirse por accidente en el futuro."""
    sig = inspect.signature(DecisionViewport.compute_target_span)
    param_names = [p.lower() for p in sig.parameters]
    assert not any("player" in name for name in param_names)
    assert set(sig.parameters.keys()) == {"self", "candidate_positions", "fallback_bounds"}


def test_compute_target_span_fallback_for_fewer_than_two_candidates():
    rect = pygame.Rect(0, 0, 600, 600)
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)
    bounds = ((-5.0, 5.0), (-5.0, 5.0))

    assert viewport.compute_target_span([], fallback_bounds=bounds) == pytest.approx(10.0)
    assert viewport.compute_target_span([(1.0, 1.0)], fallback_bounds=bounds) == pytest.approx(10.0)


def test_compute_target_span_matches_hand_calculated_formula():
    """Caso exacto, calculado a mano: 5 puntos en cruz alrededor del
    origen, cada uno a distancia 1 del centroide (que coincide con el
    origen). radio_máximo=1 -> diámetro=2 -> span = 2 * zoom_margin."""
    rect = pygame.Rect(0, 0, 600, 600)
    bounds = ((-100.0, 100.0), (-100.0, 100.0))  # bounds amplio: el techo no debe interferir

    viewport = DecisionViewport(playable_rect=rect, grid_size=50, zoom_margin=1.4)
    cross_points = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (0.0, 0.0)]
    span = viewport.compute_target_span(cross_points, fallback_bounds=bounds)
    assert span == pytest.approx(2.0 * 1.4)

    # El mismo patrón, desplazado lejos del origen: el centroide se mueve
    # con los puntos, pero el radio (y por tanto el span) debe ser idéntico.
    shifted_points = [(6.0, 5.0), (4.0, 5.0), (5.0, 6.0), (5.0, 4.0), (5.0, 5.0)]
    span_shifted = viewport.compute_target_span(shifted_points, fallback_bounds=bounds)
    assert span_shifted == pytest.approx(span)


def test_compute_target_span_zoom_margin_is_configurable():
    rect = pygame.Rect(0, 0, 600, 600)
    bounds = ((-100.0, 100.0), (-100.0, 100.0))
    cross_points = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (0.0, 0.0)]

    viewport_tight = DecisionViewport(playable_rect=rect, grid_size=50, zoom_margin=1.1)
    viewport_loose = DecisionViewport(playable_rect=rect, grid_size=50, zoom_margin=2.0)

    span_tight = viewport_tight.compute_target_span(cross_points, fallback_bounds=bounds)
    span_loose = viewport_loose.compute_target_span(cross_points, fallback_bounds=bounds)

    assert span_tight == pytest.approx(2.0 * 1.1)
    assert span_loose == pytest.approx(2.0 * 2.0)
    assert span_loose > span_tight


def test_compute_target_span_is_invariant_to_a_nearby_reference_point():
    """Regresión directa del bug reportado: antes, incluir la posición del
    jugador en el mismo conjunto de puntos usado para medir dispersión
    hacía que ACERCARSE a un candidato disparara zoom incorrecto. Ahora,
    ni siquiera existe una forma de pasarle esa posición a la función —
    este test lo confirma comparando el span con el mismo conjunto de
    candidatos, sin importar qué tan cerca esté un punto de referencia
    externo de cualquiera de ellos (simulando distintas posiciones del
    jugador que NUNCA se le pasan a la función)."""
    rect = pygame.Rect(0, 0, 600, 600)
    bounds = ((-100.0, 100.0), (-100.0, 100.0))
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)

    candidates = [(3.0, 3.0), (5.0, 3.0), (3.0, 5.0), (3.0, 1.0), (1.0, 3.0)]
    span_reference = viewport.compute_target_span(candidates, fallback_bounds=bounds)

    # Ninguna de estas "posiciones hipotéticas del jugador" se le pasa a
    # compute_target_span — la firma no lo permite. El span debe ser
    # idéntico sin importar cuál sea, porque simplemente no participan.
    hypothetical_player_positions = [(3.0, 3.0), (5.0, 3.0), (3.0, 3.001), (-50.0, 50.0)]
    for _ in hypothetical_player_positions:
        span_again = viewport.compute_target_span(candidates, fallback_bounds=bounds)
        assert span_again == pytest.approx(span_reference)


def test_compute_target_span_has_minimum_floor_when_candidates_coincide():
    """Cuando los candidatos REALES están prácticamente superpuestos (ej.
    Nelder-Mead muy cerca de converger), el radio es ~0 — se usa un piso
    mínimo en vez de producir un span de 0 (división por cero disfrazada).
    Esto es DISTINTO del bug original: aquí el radio es casi cero porque
    los candidatos matemáticos casi coinciden, no por la posición del
    jugador (que ni siquiera es un parámetro de esta función)."""
    rect = pygame.Rect(0, 0, 600, 600)
    bounds = ((-5.0, 5.0), (-5.0, 5.0))
    viewport = DecisionViewport(playable_rect=rect, grid_size=50)

    nearly_identical = [(1.0, 1.0), (1.0000001, 1.0), (1.0, 1.0000001), (1.0, 1.0), (1.0, 1.0)]
    span = viewport.compute_target_span(nearly_identical, fallback_bounds=bounds)
    assert span > 0.0
    assert span < 0.01  # muchísimo más cerrado que el dominio (10 unidades)


def test_compute_target_span_never_exceeds_bounds_cap():
    """Red de seguridad: candidatos muy dispersos (ej. Recocido Simulado
    con temperatura inicial alta) no deben producir un span mayor al
    dominio completo de la función."""
    rect = pygame.Rect(0, 0, 600, 600)
    bounds = ((-2.0, 2.0), (-1.0, 3.0))  # dominio de 4x4, como Rosenbrock
    viewport = DecisionViewport(playable_rect=rect, grid_size=50, zoom_margin=1.4)

    very_spread_points = [(20.0, 0.0), (-20.0, 0.0), (0.0, 20.0), (0.0, -20.0), (0.0, 0.0)]
    span = viewport.compute_target_span(very_spread_points, fallback_bounds=bounds)

    bounds_extent = max(bounds[0][1] - bounds[0][0], bounds[1][1] - bounds[1][0])
    assert span <= bounds_extent * 1.1 + 1e-6


# ----------------------------------------------------------------------
# CameraFollow: sin cambios respecto a la revisión anterior — sigue siendo
# el mecanismo de seguimiento continuo, ahora persiguiendo un objetivo
# calculado con la nueva separación centro/span.
# ----------------------------------------------------------------------

def test_camera_follow_converges_toward_target_over_time():
    follow = CameraFollow(center_lerp_rate=6.0, span_lerp_rate=4.0)
    follow.snap_to(ViewportState(center=(0.0, 0.0), span=10.0))
    target = ViewportState(center=(4.0, 0.0), span=2.0)

    follow.update(dt=0.05, target=target)
    mid_state = follow.state
    assert 0.0 < mid_state.center[0] < 4.0
    assert 2.0 < mid_state.span < 10.0

    for _ in range(200):
        follow.update(dt=0.016, target=target)
    final_state = follow.state
    assert final_state.center[0] == pytest.approx(4.0, abs=0.01)
    assert final_state.span == pytest.approx(2.0, abs=0.01)


def test_camera_follow_snap_to_teleports_without_animating():
    follow = CameraFollow()
    state = ViewportState(center=(7.0, -3.0), span=1.5)
    follow.snap_to(state)
    assert follow.state.center == state.center
    assert follow.state.span == pytest.approx(state.span)


def test_camera_follow_is_framerate_independent():
    """Propiedad central del suavizado exponencial: converger a la MISMA
    posición aproximada tras el mismo tiempo TOTAL transcurrido, sin
    importar si ese tiempo se dividió en pocos frames grandes o muchos
    frames pequeños."""
    target = ViewportState(center=(10.0, 0.0), span=10.0)

    follow_few_large_frames = CameraFollow(center_lerp_rate=3.0, span_lerp_rate=3.0)
    follow_few_large_frames.snap_to(ViewportState(center=(0.0, 0.0), span=10.0))
    for _ in range(2):
        follow_few_large_frames.update(dt=0.5, target=target)

    follow_many_small_frames = CameraFollow(center_lerp_rate=3.0, span_lerp_rate=3.0)
    follow_many_small_frames.snap_to(ViewportState(center=(0.0, 0.0), span=10.0))
    for _ in range(60):
        follow_many_small_frames.update(dt=1.0 / 60, target=target)

    assert follow_few_large_frames.state.center[0] == pytest.approx(
        follow_many_small_frames.state.center[0], abs=0.05
    )
# IRONEDIT:1783483892:d9b8b87321a2b15a878569b82bde955a3386fa65276cd3743397bf412da086fa
