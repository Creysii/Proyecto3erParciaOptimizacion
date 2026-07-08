"""
Rastrigin (2D, A=10): f(x,y) = 20 + [x^2 - 10cos(2*pi*x)] + [y^2 - 10cos(2*pi*y)]

Terreno con muchísimos mínimos locales de tamaño comparable, oscilando
alrededor de una tendencia cuadrática general. Es la función que la
rúbrica señala explícitamente como ideal para mostrar cuándo un algoritmo
determinista (Hooke-Jeeves, Newton) queda atrapado en un óptimo local,
frente a uno que puede escapar probabilísticamente (Recocido Simulado).

Derivación:
  df/dx = 2x + 20*pi*sin(2*pi*x)
  df/dy = 2y + 20*pi*sin(2*pi*y)
  Hxx   = 2 + 40*pi^2*cos(2*pi*x)
  Hyy   = 2 + 40*pi^2*cos(2*pi*y)
  Hxy   = 0   <- los términos en x e y están completamente desacoplados,
               así que la Hessiana SIEMPRE es diagonal. Esto es visualmente
               relevante: la elipse de la aproximación cuadrática de Newton
               siempre tendrá sus ejes alineados con los ejes cartesianos
               aquí, pero oscilando violentamente de tamaño de un punto a
               otro — una buena pista visual de por qué Newton se confunde
               en terrenos muy oscilantes.
"""

from __future__ import annotations

import math

from optimization.terrain_functions.base import TerrainFunction

_A = 10.0
_TWO_PI = 2.0 * math.pi


class Rastrigin(TerrainFunction):
    id = "rastrigin"
    name = "Rastrigin"
    bounds = ((-5.12, 5.12), (-5.12, 5.12))
    global_optimum_position = (0.0, 0.0)
    global_optimum_value = 0.0

    def evaluate(self, x: float, y: float) -> float:
        return (
            2 * _A
            + (x**2 - _A * math.cos(_TWO_PI * x))
            + (y**2 - _A * math.cos(_TWO_PI * y))
        )

    def gradient(self, x: float, y: float) -> tuple[float, float]:
        dfdx = 2 * x + _A * _TWO_PI * math.sin(_TWO_PI * x)
        dfdy = 2 * y + _A * _TWO_PI * math.sin(_TWO_PI * y)
        return (dfdx, dfdy)

    def hessian(self, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]]:
        hxx = 2 + _A * _TWO_PI**2 * math.cos(_TWO_PI * x)
        hyy = 2 + _A * _TWO_PI**2 * math.cos(_TWO_PI * y)
        return ((hxx, 0.0), (0.0, hyy))
# IRONEDIT:1783483892:427748c98bee7e27e5f475f2852463083f4bed764e822054689d162600f41212
