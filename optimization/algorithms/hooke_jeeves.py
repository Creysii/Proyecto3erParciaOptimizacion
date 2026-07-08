"""
Hooke-Jeeves.

Estado interno: posición actual (x,y) y tamaño de paso Delta.

Los 5 candidatos en cada punto de decisión:
  - 4 movimientos exploratorios: (+Delta,0), (-Delta,0), (0,+Delta), (0,-Delta)
  - 1 "salto de patrón": si el mejor de los 4 exploratorios mejora sobre la
    posición actual, se extrapola al DOBLE de Delta en esa misma dirección
    (la idea real de Hooke-Jeeves: comprometerse más fuerte con una
    dirección que ya demostró ser buena). Si ninguno de los 4 mejora, el
    candidato de patrón es la posición actual sin cambio (ya no hay
    dirección prometedora que extrapolar).

Regla de actualización de Delta (aplicada sobre lo que el JUGADOR elige,
no sobre una búsqueda automática): si el candidato aceptado no mejora la
f respecto a la posición anterior, Delta se reduce a la mitad — igual que
el algoritmo real reduce su radio de búsqueda cuando la exploración falla.

Criterio de paro: Delta < epsilon.
"""

from __future__ import annotations

from optimization.algorithms.base import Candidate, OptimizationAlgorithm, label_candidates_by_rank
from optimization.terrain_functions.base import TerrainFunction

INITIAL_DELTA = 0.75
EPSILON_DELTA = 1e-3


class HookeJeeves(OptimizationAlgorithm):
    id = "hooke_jeeves"
    name = "Hooke-Jeeves"

    def initialize(self, x0: tuple[float, float], terrain: TerrainFunction) -> None:
        self.terrain = terrain
        self.position = x0
        self.value = terrain.evaluate(*x0)
        self.delta = INITIAL_DELTA
        self.iterations_used = 0

    def get_candidates(self) -> list[Candidate]:
        x, y = self.position
        d = self.delta
        terrain = self.terrain

        axis_moves = {
            "+delta_x": (x + d, y),
            "-delta_x": (x - d, y),
            "+delta_y": (x, y + d),
            "-delta_y": (x, y - d),
        }
        axis_f = {label: terrain.evaluate(*pos) for label, pos in axis_moves.items()}

        best_axis_label = min(axis_f, key=lambda k: axis_f[k])
        best_axis_pos = axis_moves[best_axis_label]
        best_axis_f = axis_f[best_axis_label]

        if best_axis_f < self.value:
            # Extrapolar al doble de distancia en la dirección que mejoró.
            bx, by = best_axis_pos
            pattern_pos = (x + 2 * (bx - x), y + 2 * (by - y))
        else:
            # Ninguna dirección mejoró: no hay patrón que extrapolar.
            pattern_pos = (x, y)
        pattern_f = terrain.evaluate(*pattern_pos)

        positions = list(axis_moves.values()) + [pattern_pos]
        f_values = list(axis_f.values()) + [pattern_f]
        labels = label_candidates_by_rank(f_values)
        operation_labels = list(axis_moves.keys()) + ["patron"]

        return [
            Candidate(position=positions[i], f_value=f_values[i], quality_label=labels[i],
                      operation_label=operation_labels[i])
            for i in range(5)
        ]

    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        improved = candidate.f_value < self.value
        self.position = candidate.position
        self.value = candidate.f_value
        if not improved:
            self.delta *= 0.5
        self.iterations_used += 1
        return candidate

    def has_converged(self) -> bool:
        return self.delta < EPSILON_DELTA

    def get_convergence_indicator(self) -> float:
        return self.delta

    def get_current_position(self) -> tuple[float, float]:
        return self.position

    def get_current_value(self) -> float:
        return self.value
# IRONEDIT:1783483892:7f0b2e3b9814c67f5ff1835b78bac10d624f76ac39b177a4ef029c06ecbc233e
