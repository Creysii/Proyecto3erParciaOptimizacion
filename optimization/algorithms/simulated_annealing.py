"""
Recocido Simulado (Simulated Annealing).

Estado interno: posición actual, valor de f actual, temperatura T.

Los 5 candidatos son vecinos aleatorios dentro de un radio (que se reduce
junto con T, para reflejar cómo el algoritmo real explora un vecindario
cada vez más chico conforme se enfría). Se etiquetan por calidad relativa
igual que los demás algoritmos — pero, a diferencia de todos los otros
tres, la elección del jugador NO garantiza la aceptación: al confirmar,
se ejecuta el mecanismo real de aceptación:

  - Si el candidato es mejor (menor f) que la posición actual: se acepta
    SIEMPRE (así funciona el algoritmo real).
  - Si es peor: se acepta con probabilidad exp(-DeltaE / T), con una
    tirada aleatoria real en ese momento — el jugador puede "perder" el
    movimiento incluso habiendo elegido el candidato que consideraba mejor.

Independientemente de si se acepta o rechaza, T se enfría (T *= alpha) y
la iteración cuenta como realizada — así es como funciona Recocido
Simulado real: cada iteración enfría el sistema, se acepte o no el paso.

Criterio de paro: T < epsilon.
"""

from __future__ import annotations

import math
import random

from optimization.algorithms.base import Candidate, OptimizationAlgorithm, label_candidates_by_rank
from optimization.terrain_functions.base import TerrainFunction

INITIAL_TEMPERATURE = 8.0
COOLING_RATE = 0.90  # T_nuevo = T_actual * COOLING_RATE, cada iteración
EPSILON_TEMPERATURE = 0.05
BASE_NEIGHBOR_RADIUS = 1.2


class SimulatedAnnealing(OptimizationAlgorithm):
    id = "simulated_annealing"
    name = "Recocido Simulado"

    def initialize(self, x0: tuple[float, float], terrain: TerrainFunction) -> None:
        self.terrain = terrain
        self.position = x0
        self.value = terrain.evaluate(*x0)
        self.temperature = INITIAL_TEMPERATURE
        self.iterations_used = 0

    def _current_radius(self) -> float:
        # El radio de exploración se reduce junto con la temperatura,
        # reflejando visualmente el enfriamiento del sistema.
        fraction = self.temperature / INITIAL_TEMPERATURE
        return max(0.15, BASE_NEIGHBOR_RADIUS * fraction)

    def get_neighbor_radius(self) -> float:
        """Expone el radio actual para el renderer (la nube de puntos
        visual) — el algoritmo sigue siendo la única fuente de verdad de
        su propio parámetro, el renderer no debe tocar estado interno."""
        return self._current_radius()

    def get_candidates(self) -> list[Candidate]:
        x, y = self.position
        radius = self._current_radius()
        terrain = self.terrain

        positions = []
        f_values = []
        for _ in range(5):
            dx = random.uniform(-radius, radius)
            dy = random.uniform(-radius, radius)
            pos = (x + dx, y + dy)
            positions.append(pos)
            f_values.append(terrain.evaluate(*pos))

        labels = label_candidates_by_rank(f_values)

        candidates = []
        for i in range(5):
            delta_e = f_values[i] - self.value
            if delta_e <= 0:
                acceptance_probability = 1.0
            else:
                acceptance_probability = math.exp(-delta_e / self.temperature)

            candidates.append(
                Candidate(
                    position=positions[i],
                    f_value=f_values[i],
                    quality_label=labels[i],
                    acceptance_probability=acceptance_probability,
                    operation_label=f"vecino_{i+1}",
                )
            )
        return candidates

    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        """Ejecuta la tirada probabilística REAL. Si se rechaza, la
        posición no cambia — se devuelve un Candidate que representa
        'quedarse donde estabas', con quality_label='rechazado' para que
        la UI pueda distinguir claramente este caso."""
        delta_e = candidate.f_value - self.value
        accepted: bool
        if delta_e <= 0:
            accepted = True
        else:
            probability = math.exp(-delta_e / self.temperature)
            accepted = random.random() < probability

        self.temperature *= COOLING_RATE
        self.iterations_used += 1

        if accepted:
            self.position = candidate.position
            self.value = candidate.f_value
            return candidate

        # Rechazado: el jugador eligió este candidato, pero el dado no
        # favoreció la aceptación — la posición se mantiene igual.
        return Candidate(
            position=self.position,
            f_value=self.value,
            quality_label="rechazado",
            acceptance_probability=candidate.acceptance_probability,
            operation_label="rechazado",
        )

    def has_converged(self) -> bool:
        return self.temperature < EPSILON_TEMPERATURE

    def get_convergence_indicator(self) -> float:
        return self.temperature

    def get_current_position(self) -> tuple[float, float]:
        return self.position

    def get_current_value(self) -> float:
        return self.value
# IRONEDIT:1783483892:2cdacb0c508ac6ab504257ba1254219bfcfaafb9c63b0890ce01b85dd1c71e6d
