"""
RunResult: snapshot completo y fiel de una corrida terminada. No calcula
nada por sí mismo (salvo relative_progress, una métrica derivada pura) —
su único trabajo es capturar con precisión qué pasó, para que cualquier
fórmula de recompensa (hoy un placeholder, después algo balanceado con
playtesting real) pueda calcularse exclusivamente a partir de este objeto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RunResult:
    terrain_function_id: str
    algorithm_id: str
    iterations_used: int
    x_start: tuple[float, float]
    x_final: tuple[float, float]
    f_start: float
    f_final: float
    global_optimum_value: float
    ended_by_player: bool  # True = botón de victoria; False = límite de seguridad

    def relative_progress(self, tolerance: float = 1e-6) -> float:
        """(f_start - f_final) / (f_start - global_optimum_value).

        1.0 = llegaste exactamente al óptimo global.
        0.0 = no mejoraste nada respecto a tu punto de partida.

        Caso límite: si el punto de partida ya estaba prácticamente en el
        óptimo global, el denominador es ~0 — en ese caso, se define el
        progreso como 1.0 (ya estabas donde debías estar)."""
        denominator = self.f_start - self.global_optimum_value
        if abs(denominator) < tolerance:
            return 1.0
        return (self.f_start - self.f_final) / denominator


class RewardStrategy(ABC):
    @abstractmethod
    def compute(self, run_result: RunResult) -> int:
        raise NotImplementedError


class PlaceholderRewardStrategy(RewardStrategy):
    """Implementación placeholder — se reemplaza tras el primer
    playtesting real con una fórmula balanceada. Por ahora: 100 puntos
    escalados por el progreso relativo y por el multiplicador de la tabla
    algoritmo x función (que hoy son todos 1.0, sin efecto real)."""

    def __init__(self, scoring_multipliers: dict[tuple[str, str], float]) -> None:
        self._scoring_multipliers = scoring_multipliers

    def compute(self, run_result: RunResult) -> int:
        multiplier = self._scoring_multipliers.get(
            (run_result.algorithm_id, run_result.terrain_function_id), 1.0
        )
        progress = run_result.relative_progress()
        return max(0, int(round(100 * progress * multiplier)))
# IRONEDIT:1783483892:b9700acb0b96235e9f75b5fc897c42774a899f06ffdc2976582e6ca2160380f5
