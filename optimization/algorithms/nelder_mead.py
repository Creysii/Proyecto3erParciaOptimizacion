"""
Nelder-Mead (Simplex).

Estado interno: un simplex de 3 vértices (x,y) en 2D, cada uno con su f
ya evaluada.

Adaptación de diseño explícita (documentada aquí a propósito, no un
descuido): el algoritmo real decide de forma determinista cuál de las 4
operaciones aplicar en cada iteración, según reglas de comparación. Para
esta implementación, en cambio, se muestran SIEMPRE las 5 posibles
operaciones como candidatos (reflexión, expansión, contracción exterior,
contracción interior, shrink), rankeadas por calidad, y el jugador elige
cuál aplicar — el "punto donde está parado el jugador" se define como el
MEJOR vértice del simplex actual (no el peor), porque es el vértice que
NO se toca en la mayoría de las operaciones y por tanto sirve como ancla
estable de posición.

Coeficientes estándar: alpha=1 (reflexión), gamma=2 (expansión),
rho=0.5 (contracción), sigma=0.5 (shrink).

Con centroide c = promedio de los 2 mejores vértices (excluyendo el peor,
w):
  reflexión            xr  = c + alpha*(c - w)
  expansión             xe  = c + gamma*(xr - c)
  contracción exterior  xco = c + rho*(xr - c)
  contracción interior  xci = c + rho*(w - c)
  shrink (representativo) = mejor + sigma*(w - mejor)
    (el shrink real mueve TODOS los vértices excepto el mejor; el punto de
    arriba es solo dónde terminaría el peor vértice bajo esa operación,
    usado como su "candidato representativo" en pantalla)

Criterio de paro: dispersión de f entre los 3 vértices (f_peor - f_mejor) < epsilon.
"""

from __future__ import annotations

from optimization.algorithms.base import Candidate, OptimizationAlgorithm, label_candidates_by_rank
from optimization.terrain_functions.base import TerrainFunction

INITIAL_EDGE_LENGTH = 1.0
ALPHA = 1.0
GAMMA = 2.0
RHO = 0.5
SIGMA = 0.5
EPSILON_SPREAD = 1e-3


class _Vertex:
    __slots__ = ("position", "f_value")

    def __init__(self, position: tuple[float, float], f_value: float) -> None:
        self.position = position
        self.f_value = f_value


class NelderMead(OptimizationAlgorithm):
    id = "nelder_mead"
    name = "Nelder-Mead"

    def initialize(self, x0: tuple[float, float], terrain: TerrainFunction) -> None:
        self.terrain = terrain
        x, y = x0
        e = INITIAL_EDGE_LENGTH
        raw_positions = [(x, y), (x + e, y), (x, y + e)]
        self.simplex = [_Vertex(p, terrain.evaluate(*p)) for p in raw_positions]
        self._sort_simplex()
        self.iterations_used = 0

    def _sort_simplex(self) -> None:
        self.simplex.sort(key=lambda v: v.f_value)

    @property
    def _best(self) -> _Vertex:
        return self.simplex[0]

    @property
    def _second(self) -> _Vertex:
        return self.simplex[1]

    @property
    def _worst(self) -> _Vertex:
        return self.simplex[2]

    def _centroid_excluding_worst(self) -> tuple[float, float]:
        bx, by = self._best.position
        sx, sy = self._second.position
        return ((bx + sx) / 2.0, (by + sy) / 2.0)

    def get_candidates(self) -> list[Candidate]:
        terrain = self.terrain
        c = self._centroid_excluding_worst()
        w = self._worst.position
        b = self._best.position

        xr = (c[0] + ALPHA * (c[0] - w[0]), c[1] + ALPHA * (c[1] - w[1]))
        xe = (c[0] + GAMMA * (xr[0] - c[0]), c[1] + GAMMA * (xr[1] - c[1]))
        xco = (c[0] + RHO * (xr[0] - c[0]), c[1] + RHO * (xr[1] - c[1]))
        xci = (c[0] + RHO * (w[0] - c[0]), c[1] + RHO * (w[1] - c[1]))
        xsh = (b[0] + SIGMA * (w[0] - b[0]), b[1] + SIGMA * (w[1] - b[1]))

        positions = [xr, xe, xco, xci, xsh]
        f_values = [terrain.evaluate(*p) for p in positions]
        labels = label_candidates_by_rank(f_values)
        operation_labels = [
            "reflexion", "expansion", "contraccion_exterior", "contraccion_interior", "shrink",
        ]

        return [
            Candidate(position=positions[i], f_value=f_values[i], quality_label=labels[i],
                      operation_label=operation_labels[i])
            for i in range(5)
        ]

    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        if candidate.operation_label == "shrink":
            # El shrink real mueve TODOS los vértices excepto el mejor.
            best_pos = self._best.position
            for vertex in (self._second, self._worst):
                nx = best_pos[0] + SIGMA * (vertex.position[0] - best_pos[0])
                ny = best_pos[1] + SIGMA * (vertex.position[1] - best_pos[1])
                vertex.position = (nx, ny)
                vertex.f_value = self.terrain.evaluate(nx, ny)
        else:
            # Las otras 4 operaciones reemplazan únicamente al peor vértice.
            self._worst.position = candidate.position
            self._worst.f_value = candidate.f_value

        self._sort_simplex()
        self.iterations_used += 1
        return candidate

    def has_converged(self) -> bool:
        return (self._worst.f_value - self._best.f_value) < EPSILON_SPREAD

    def get_convergence_indicator(self) -> float:
        return self._worst.f_value - self._best.f_value

    def get_current_position(self) -> tuple[float, float]:
        return self._best.position

    def get_current_value(self) -> float:
        return self._best.f_value

    def get_simplex_positions(self) -> list[tuple[float, float]]:
        """Método adicional específico de Nelder-Mead, usado por el
        renderer para dibujar el triángulo completo del simplex."""
        return [v.position for v in self.simplex]
# IRONEDIT:1783483892:11691d6c0842bc428872b54dd613c40f1ac8dce9590b74bdd510ec92e8d86508
