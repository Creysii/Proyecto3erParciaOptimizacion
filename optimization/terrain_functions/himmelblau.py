"""
Himmelblau: f(x,y) = (x^2+y-11)^2 + (x+y^2-7)^2

Tiene CUATRO mínimos globales distintos, todos con f=0:
  (3.0, 2.0), (-2.805118, 3.131312), (-3.779310, -3.283186), (3.584428, -1.848126)

Ideal para mostrar cómo el punto inicial x0 determina a cuál de los cuatro
converge el algoritmo — la "elección" de x0 por parte del jugador tiene
consecuencias reales y visibles aquí.

Derivación (con A = x^2+y-11, B = x+y^2-7):
  df/dx = 4xA + 2B
  df/dy = 2A + 4yB
  Hxx   = 12x^2 + 4y - 42
  Hyy   = 12y^2 + 4x - 26
  Hxy   = Hyx = 4x + 4y
"""

from __future__ import annotations

from optimization.terrain_functions.base import TerrainFunction


class Himmelblau(TerrainFunction):
    id = "himmelblau"
    name = "Himmelblau"
    bounds = ((-5.0, 5.0), (-5.0, 5.0))
    # Representativo: existen 3 más, todos con el mismo global_optimum_value.
    global_optimum_position = (3.0, 2.0)
    global_optimum_value = 0.0

    def evaluate(self, x: float, y: float) -> float:
        a = x**2 + y - 11
        b = x + y**2 - 7
        return a**2 + b**2

    def gradient(self, x: float, y: float) -> tuple[float, float]:
        a = x**2 + y - 11
        b = x + y**2 - 7
        dfdx = 4 * x * a + 2 * b
        dfdy = 2 * a + 4 * y * b
        return (dfdx, dfdy)

    def hessian(self, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]]:
        hxx = 12 * x**2 + 4 * y - 42
        hyy = 12 * y**2 + 4 * x - 26
        hxy = 4 * x + 4 * y
        return ((hxx, hxy), (hxy, hyy))
# IRONEDIT:1783483892:80a54ef8e38aed4d4eb9237a7d13ee01345b569481f4e28008ba8d72ea7f363b
