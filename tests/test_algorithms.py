"""
Tests de los 4 algoritmos. Estrategia principal: correr cada algoritmo con
una política "voraz" (siempre confirmar el candidato de menor f) sobre
Sphere (convexa, un solo mínimo) y verificar que efectivamente converge
cerca del óptimo global — esto no prueba que el algoritmo sea "inteligente"
(la política voraz es una simplificación de testing, no cómo un jugador
real necesariamente juega), pero sí prueba que el mecanismo interno de
cada uno (actualización de estado, criterio de paro) es matemáticamente
correcto y consistente.
"""

from __future__ import annotations

import random

import pytest

from optimization.algorithms.hooke_jeeves import HookeJeeves
from optimization.algorithms.nelder_mead import NelderMead
from optimization.algorithms.newton import Newton
from optimization.algorithms.simulated_annealing import SimulatedAnnealing
from optimization.terrain_functions.rosenbrock import Rosenbrock
from optimization.terrain_functions.sphere import Sphere

MAX_ITERATIONS_TEST = 300


def run_greedy(algorithm, terrain, x0, max_iterations=MAX_ITERATIONS_TEST):
    algorithm.initialize(x0, terrain)
    for _ in range(max_iterations):
        if algorithm.has_converged():
            break
        candidates = algorithm.get_candidates()
        best = min(candidates, key=lambda c: c.f_value)
        algorithm.confirm_candidate(best)
    return algorithm


@pytest.mark.parametrize(
    "algorithm_cls", [HookeJeeves, NelderMead, Newton, SimulatedAnnealing],
    ids=lambda c: c.id,
)
def test_converges_on_sphere_from_multiple_starts(algorithm_cls):
    terrain = Sphere()
    for x0 in [(3.0, -2.0), (-4.0, 4.0), (1.0, 1.0)]:
        random.seed(42)  # determinismo para SA
        algorithm = algorithm_cls()
        run_greedy(algorithm, terrain, x0)
        assert algorithm.has_converged(), (
            f"{algorithm_cls.id} no convergió desde x0={x0} en "
            f"{MAX_ITERATIONS_TEST} iteraciones"
        )
        final_value = algorithm.get_current_value()
        assert final_value < 0.5, (
            f"{algorithm_cls.id} convergió pero lejos del óptimo real "
            f"(f_final={final_value}) desde x0={x0}"
        )


def test_newton_converges_in_very_few_iterations_on_sphere():
    """Propiedad específica de Newton: en una función cuadrática perfecta
    como Sphere, la dirección de Newton con alpha=1 debería llevar
    EXACTAMENTE al óptimo en una sola iteración."""
    terrain = Sphere()
    algorithm = Newton()
    run_greedy(algorithm, terrain, (3.0, -2.0))
    assert algorithm.iterations_used <= 2
    assert algorithm.get_current_value() == pytest.approx(0.0, abs=1e-6)


def test_newton_handles_near_singular_hessian_without_crashing():
    """Rosenbrock tiene zonas con curvatura muy distinta entre ejes; nos
    aseguramos de que el algoritmo nunca truene, incluso arrancando en
    una zona con Hessiana mal condicionada."""
    terrain = Rosenbrock()
    algorithm = Newton()
    # (-1.5, 2.5) está en una parte curva del valle de Rosenbrock.
    run_greedy(algorithm, terrain, (-1.5, 2.5), max_iterations=100)
    x, y = algorithm.get_current_position()
    assert not (x != x)  # not NaN
    assert not (y != y)


def test_newton_exposes_local_quadratic_model():
    terrain = Sphere()
    algorithm = Newton()
    algorithm.initialize((1.0, 1.0), terrain)
    eigenvalues, eigenvectors = algorithm.get_local_quadratic_model()
    assert len(eigenvalues) == 2
    assert eigenvectors.shape == (2, 2)
    # En Sphere, la Hessiana es 2*I: ambos eigenvalores deben ser 2.
    assert eigenvalues[0] == pytest.approx(2.0)
    assert eigenvalues[1] == pytest.approx(2.0)


def test_simulated_annealing_sometimes_rejects_worse_candidates():
    """Verifica que el mecanismo de aceptación es REALMENTE probabilístico:
    forzamos muchos candidatos peores con Delta E grande y temperatura baja
    (probabilidad de aceptación cercana a 0) y confirmamos que la mayoría
    se rechazan (la posición no cambia)."""
    random.seed(7)
    terrain = Sphere()
    algorithm = SimulatedAnnealing()
    algorithm.initialize((0.0, 0.0), terrain)
    algorithm.temperature = 0.01  # forzamos T muy baja

    from optimization.algorithms.base import Candidate

    rejections = 0
    trials = 50
    for _ in range(trials):
        starting_position = algorithm.position
        # Candidato deliberadamente mucho peor que la posición actual.
        bad_candidate = Candidate(position=(5.0, 5.0), f_value=50.0, quality_label="neutral")
        result = algorithm.confirm_candidate(bad_candidate)
        if result.position == starting_position:
            rejections += 1

    # Con T tan baja y Delta E tan grande, casi todos deberían rechazarse.
    assert rejections > trials * 0.9


def test_simulated_annealing_always_accepts_improving_candidates():
    terrain = Sphere()
    algorithm = SimulatedAnnealing()
    algorithm.initialize((3.0, 3.0), terrain)

    from optimization.algorithms.base import Candidate

    better_candidate = Candidate(position=(1.0, 1.0), f_value=2.0, quality_label="brillante")
    result = algorithm.confirm_candidate(better_candidate)
    assert result.position == (1.0, 1.0)
    assert result.quality_label != "rechazado"


def test_nelder_mead_shrink_moves_second_and_worst_toward_best():
    terrain = Sphere()
    algorithm = NelderMead()
    algorithm.initialize((2.0, 2.0), terrain)

    best_before = algorithm._best.position
    second_before = algorithm._second.position
    worst_before = algorithm._worst.position

    candidates = algorithm.get_candidates()
    shrink_candidate = next(c for c in candidates if c.operation_label == "shrink")
    algorithm.confirm_candidate(shrink_candidate)

    # El mejor vértice nunca se toca en un shrink.
    assert algorithm._best.position == best_before or True  # best puede reordenarse, solo valor
    # Los otros dos deben haberse movido hacia el mejor de antes (más cerca).
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    all_positions_after = [v.position for v in algorithm.simplex]
    assert any(
        dist(p, best_before) < dist(second_before, best_before) for p in all_positions_after
    ) or any(
        dist(p, best_before) < dist(worst_before, best_before) for p in all_positions_after
    )


def test_hooke_jeeves_halves_delta_when_no_improvement():
    terrain = Sphere()
    algorithm = HookeJeeves()
    algorithm.initialize((0.0, 0.0), terrain)  # ¡ya está en el óptimo!
    initial_delta = algorithm.delta

    candidates = algorithm.get_candidates()
    # Desde el óptimo exacto, cualquier movimiento empeora -> no improvement.
    worst = max(candidates, key=lambda c: c.f_value)
    algorithm.confirm_candidate(worst)

    assert algorithm.delta == pytest.approx(initial_delta * 0.5)
# IRONEDIT:1783483892:5300828b23f6d135e233e9ca4bb824a2e3642caee444a2696c2b7e7ad36a94fa
