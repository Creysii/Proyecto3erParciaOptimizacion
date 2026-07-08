"""
Verifica que gradient()/hessian() de cada TerrainFunction coincidan con
una aproximación numérica por diferencias finitas centradas — esto NO
significa que el juego use diferencias finitas (siempre usa las fórmulas
analíticas), es solo la forma estándar de detectar un error de álgebra al
derivar a mano, comparando contra un método independiente y confiable.

También verifica que el punto reportado como global_optimum_position sea
efectivamente un punto crítico (gradiente ~0) con el valor de f esperado.
"""

from __future__ import annotations

import math

import pytest

from optimization.terrain_functions.himmelblau import Himmelblau
from optimization.terrain_functions.rastrigin import Rastrigin
from optimization.terrain_functions.rosenbrock import Rosenbrock
from optimization.terrain_functions.sphere import Sphere

ALL_FUNCTIONS = [Sphere(), Himmelblau(), Rastrigin(), Rosenbrock()]

# Puntos de prueba genéricos (evitando simetrías que podrían ocultar errores
# de signo, como x=0 o x=y).
TEST_POINTS = [(0.7, -1.3), (2.1, 0.4), (-1.5, 2.8), (0.05, -0.05)]

H = 1e-6  # paso para diferencias finitas


def numeric_gradient(func, x, y):
    dfdx = (func.evaluate(x + H, y) - func.evaluate(x - H, y)) / (2 * H)
    dfdy = (func.evaluate(x, y + H) - func.evaluate(x, y - H)) / (2 * H)
    return dfdx, dfdy


def numeric_hessian(func, x, y):
    # Segunda derivada central estándar; usamos un H más grande aquí
    # porque la resta de diferencias finitas de segundo orden amplifica
    # el error de redondeo si H es demasiado pequeño.
    h = 1e-4
    hxx = (func.evaluate(x + h, y) - 2 * func.evaluate(x, y) + func.evaluate(x - h, y)) / h**2
    hyy = (func.evaluate(x, y + h) - 2 * func.evaluate(x, y) + func.evaluate(x, y - h)) / h**2
    hxy = (
        func.evaluate(x + h, y + h)
        - func.evaluate(x + h, y - h)
        - func.evaluate(x - h, y + h)
        + func.evaluate(x - h, y - h)
    ) / (4 * h**2)
    return hxx, hxy, hyy


@pytest.mark.parametrize("func", ALL_FUNCTIONS, ids=lambda f: f.id)
@pytest.mark.parametrize("point", TEST_POINTS)
def test_gradient_matches_finite_differences(func, point):
    x, y = point
    analytic = func.gradient(x, y)
    numeric = numeric_gradient(func, x, y)
    assert analytic[0] == pytest.approx(numeric[0], abs=1e-3)
    assert analytic[1] == pytest.approx(numeric[1], abs=1e-3)


@pytest.mark.parametrize("func", ALL_FUNCTIONS, ids=lambda f: f.id)
@pytest.mark.parametrize("point", TEST_POINTS)
def test_hessian_matches_finite_differences(func, point):
    x, y = point
    (hxx, hxy), (hyx, hyy) = func.hessian(x, y)
    n_hxx, n_hxy, n_hyy = numeric_hessian(func, x, y)

    assert hxy == pytest.approx(hyx, abs=1e-9), "La Hessiana debe ser simétrica"
    assert hxx == pytest.approx(n_hxx, rel=1e-2, abs=1e-1)
    assert hyy == pytest.approx(n_hyy, rel=1e-2, abs=1e-1)
    assert hxy == pytest.approx(n_hxy, rel=1e-2, abs=1e-1)


@pytest.mark.parametrize("func", ALL_FUNCTIONS, ids=lambda f: f.id)
def test_global_optimum_is_reported_correctly(func):
    x0, y0 = func.global_optimum_position
    value_at_optimum = func.evaluate(x0, y0)
    assert value_at_optimum == pytest.approx(func.global_optimum_value, abs=1e-6)


@pytest.mark.parametrize("func", ALL_FUNCTIONS, ids=lambda f: f.id)
def test_global_optimum_is_a_critical_point(func):
    """En el óptimo global reportado, el gradiente real debe ser ~0
    (es un punto crítico), salvo casos donde el óptimo esté en el borde
    del dominio — ninguna de nuestras 4 funciones tiene esa condición."""
    x0, y0 = func.global_optimum_position
    assert func.gradient_norm(x0, y0) == pytest.approx(0.0, abs=1e-4)


def test_himmelblau_has_four_equal_global_minima():
    """Verificación específica: los 4 mínimos conocidos de Himmelblau
    deben dar todos f=0."""
    func = Himmelblau()
    known_minima = [
        (3.0, 2.0),
        (-2.805118, 3.131312),
        (-3.779310, -3.283186),
        (3.584428, -1.848126),
    ]
    for x, y in known_minima:
        assert func.evaluate(x, y) == pytest.approx(0.0, abs=1e-3)


def test_rastrigin_hessian_is_always_diagonal():
    """Propiedad estructural: al estar x e y desacopladas, Hxy debe ser
    siempre exactamente 0, para cualquier punto."""
    func = Rastrigin()
    for x, y in TEST_POINTS:
        (_, hxy), (hyx, _) = func.hessian(x, y)
        assert hxy == 0.0
        assert hyx == 0.0
# IRONEDIT:1783483892:fe9abdf70fa736d2f4cf39c5314d36e8e3622b37c3adb82efc505587a94d80a7
