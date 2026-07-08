"""
Tests del motor puro de una corrida — simula exactamente las decisiones
que tomaría un jugador (elegir x0, confirmar candidatos, declarar
victoria), sin ninguna dependencia de pygame.
"""

from __future__ import annotations

import pytest

from optimization.algorithms.newton import Newton
from optimization.algorithms.simulated_annealing import SimulatedAnnealing
from optimization.level_room import OptimizationRun, RunPhase
from optimization.terrain_functions.sphere import Sphere


def test_full_run_flow_reaches_finished_and_builds_correct_result():
    run = OptimizationRun(Sphere(), Newton())
    assert run.phase == RunPhase.CHOOSING_START

    run.choose_start((3.0, -2.0))
    assert run.phase == RunPhase.SHOWING_CANDIDATES
    assert len(run.current_candidates) == 5

    # Jugador siempre elige el mejor candidato (voraz) hasta convergencia real.
    while not run.algorithm.has_converged():
        best = min(run.current_candidates, key=lambda c: c.f_value)
        run.confirm_candidate(best)

    result = run.declare_victory()

    assert run.is_finished()
    assert result.ended_by_player is True
    assert result.terrain_function_id == "sphere"
    assert result.algorithm_id == "newton"
    assert result.x_start == (3.0, -2.0)
    assert result.f_final == pytest.approx(0.0, abs=1e-6)
    assert result.relative_progress() == pytest.approx(1.0, abs=1e-4)


def test_victory_available_from_the_very_beginning_zero_iterations():
    """Confirmado explícitamente por el equipo: el botón de victoria debe
    estar disponible desde el comienzo, sin exigir ninguna iteración."""
    run = OptimizationRun(Sphere(), Newton())
    run.choose_start((3.0, 3.0))

    result = run.declare_victory()

    assert result.iterations_used == 0
    assert result.x_final == (3.0, 3.0)
    assert result.f_final == pytest.approx(18.0)  # f(3,3) = 9+9
    # Progreso relativo debe ser 0 (no mejoró nada respecto al inicio).
    assert result.relative_progress() == pytest.approx(0.0, abs=1e-9)


def test_max_iterations_forces_finish_with_last_confirmed_position():
    """Si se alcanza el límite de seguridad, la corrida termina sola,
    usando la ÚLTIMA POSICIÓN OFICIAL CONFIRMADA (nunca un candidato sin
    confirmar) y marcando ended_by_player=False."""
    run = OptimizationRun(Sphere(), SimulatedAnnealing(), max_iterations=5)
    run.choose_start((4.0, 4.0))

    for _ in range(10):  # más que max_iterations, para forzar el corte
        if run.is_finished():
            break
        candidates = run.current_candidates
        chosen = candidates[0]
        run.confirm_candidate(chosen)

    assert run.is_finished()
    assert run.result.ended_by_player is False
    assert run.result.iterations_used == 5
    # La posición final debe coincidir exactamente con la última entrada
    # de la trayectoria (la última iteración realmente confirmada).
    assert run.result.x_final == run.trajectory[-1][0]


def test_declare_victory_before_choosing_start_raises_clean_error():
    """Regresión del bug reportado: presionar V antes de elegir x0
    (fase CHOOSING_START) producía un IndexError críptico al intentar
    leer self.trajectory[-1] de una lista vacía. Ahora debe fallar con
    un RuntimeError explícito y legible, nunca con un IndexError."""
    run = OptimizationRun(Sphere(), Newton())
    assert run.phase == RunPhase.CHOOSING_START

    with pytest.raises(RuntimeError, match="punto de partida"):
        run.declare_victory()

    # Y el estado del run no debe haberse corrompido: sigue eligible
    # para un choose_start() normal después del intento fallido.
    run.choose_start((1.0, 1.0))
    assert run.phase == RunPhase.SHOWING_CANDIDATES


def test_cannot_confirm_candidate_before_choosing_start():
    run = OptimizationRun(Sphere(), Newton())
    with pytest.raises(RuntimeError):
        run.confirm_candidate(run.current_candidates)  # ni siquiera hay candidatos aún


def test_trajectory_records_one_entry_per_confirmed_iteration_plus_start():
    run = OptimizationRun(Sphere(), Newton())
    run.choose_start((2.0, 2.0))
    assert len(run.trajectory) == 1  # solo x0

    best = min(run.current_candidates, key=lambda c: c.f_value)
    run.confirm_candidate(best)
    assert len(run.trajectory) == 2  # x0 + 1 iteración
# IRONEDIT:1783483892:c0034709fd39386144fa954ca9b28f84f2d7b30198f74dc6533e974fecf5ac6f
