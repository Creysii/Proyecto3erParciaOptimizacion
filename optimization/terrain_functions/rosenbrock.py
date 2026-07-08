"""
Rosenbrock (2D): f(x,y) = 100*(y - x^2)^2 + (1 - x)^2

La forma general de n variables dada en la rúbrica es:
  f(x) = sum_i [100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2]
Para n=2 (un solo término, i=1, x1=x, x2=y) se reduce exactamente a la
expresión de arriba.

Su característica distintiva es un valle curvo y muy estrecho (forma de
"banana") que contiene al mínimo global — la dirección de descenso más
pronunciado casi nunca apunta directamente hacia el mínimo, así que un
algoritmo que no use información de segunda derivada (Hooke-Jeeves) tiende
a avanzar en zigzags lentos a lo largo del valle, mientras que Newton,
que sí modela la curvatura, puede seguir el valle de forma mucho más
directa — siempre que la aproximación cuadrática local sea razonable.

Derivación:
  df/dx = -400*x*(y - x^2) - 2*(1 - x)
  df/dy = 200*(y - x^2)
  Hxx   = -400*y + 1200*x^2 + 2
  Hyy   = 200
  Hxy   = Hyx = -400*x
"""

from __future__ import annotations

from optimization.terrain_functions.base import TerrainFunction


class Rosenbrock(TerrainFunction):
    id = "rosenbrock"
    name = "Rosenbrock"
    bounds = ((-2.0, 2.0), (-1.0, 3.0))
    global_optimum_position = (1.0, 1.0)
    global_optimum_value = 0.0

    def evaluate(self, x: float, y: float) -> float:
        return 100.0 * (y - x**2) ** 2 + (1.0 - x) ** 2

    def gradient(self, x: float, y: float) -> tuple[float, float]:
        dfdx = -400.0 * x * (y - x**2) - 2.0 * (1.0 - x)
        dfdy = 200.0 * (y - x**2)
        return (dfdx, dfdy)

    def hessian(self, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]]:
        hxx = -400.0 * y + 1200.0 * x**2 + 2.0
        hyy = 200.0
        hxy = -400.0 * x
        return ((hxx, hxy), (hxy, hyy))
# IRONEDIT:1783483892:233cec3e0277e0ca35bede81eff24fc643df3b149f5b115de5bd7dcf5215d49d
