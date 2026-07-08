"""
Sphere: f(x,y) = x^2 + y^2

La función "caso fácil" — un solo mínimo global, curvatura constante en
todas direcciones (la Hessiana es la matriz identidad escalada por 2,
sin depender del punto). Útil para verificar que un algoritmo converge
correctamente en el escenario más benigno posible.
"""

from __future__ import annotations

from optimization.terrain_functions.base import TerrainFunction


class Sphere(TerrainFunction):
    id = "sphere"
    name = "Sphere"
    bounds = ((-5.0, 5.0), (-5.0, 5.0))
    global_optimum_position = (0.0, 0.0)
    global_optimum_value = 0.0

    def evaluate(self, x: float, y: float) -> float:
        return x**2 + y**2

    def gradient(self, x: float, y: float) -> tuple[float, float]:
        return (2.0 * x, 2.0 * y)

    def hessian(self, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]]:
        return ((2.0, 0.0), (0.0, 2.0))
# IRONEDIT:1783483892:7a8c56fe673a20cd018b0d8400586eaf91ea1421dfc401357f6580eec7da0bd7
