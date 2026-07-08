"""
Clase base para un algoritmo de optimización ("detector"). Cada algoritmo
concreto mantiene su propio estado interno (simplex, Delta, temperatura,
etc.) y expone el mismo contrato de 5 pasos:

  initialize(x0)      -> fija el estado interno desde el punto de partida
  get_candidates()    -> calcula los 5 candidatos reales desde el estado actual
  confirm_candidate() -> ejecuta el paso REAL del algoritmo, actualiza estado
  has_converged()     -> criterio de paro matemático real
  get_convergence_indicator() -> valor numérico a mostrar en el HUD

Ningún código de pygame ni de game/ debe necesitar un `if algorithm_id == ...`
en ninguna parte — todo pasa por esta única interfaz.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from optimization.terrain_functions.base import TerrainFunction

QualityLabel = str  # "brillante" | "buena" | "neutral"


@dataclass
class Candidate:
    position: tuple[float, float]
    f_value: float
    quality_label: QualityLabel
    # Solo tiene sentido para Recocido Simulado: la probabilidad real de
    # aceptación si este candidato resulta peor que la posición actual.
    # None para los demás algoritmos (su aceptación no es probabilística).
    acceptance_probability: Optional[float] = None
    # Etiqueta legible de qué operación generó este candidato (ej.
    # "reflexión", "+Delta eje X", "alpha=1.0") — puramente informativo,
    # útil para el HUD y para el mensaje post-movimiento.
    operation_label: str = ""


def label_candidates_by_rank(f_values: list[float]) -> list[QualityLabel]:
    """Rankea 5 valores de f (menor es mejor, es un problema de
    minimización) según el esquema '1 brillante, 2 buenas, 2 neutrales'
    acordado. Devuelve las etiquetas en el mismo orden que f_values
    (no ordenado), para que el llamador pueda asignarlas de vuelta a
    cada candidato en su posición original."""
    n = len(f_values)
    order = sorted(range(n), key=lambda i: f_values[i])  # índices, mejor primero

    labels_by_rank: list[QualityLabel] = []
    for rank in range(n):
        if rank == 0:
            labels_by_rank.append("brillante")
        elif rank <= 2:
            labels_by_rank.append("buena")
        else:
            labels_by_rank.append("neutral")

    result: list[QualityLabel] = [""] * n
    for rank, original_index in enumerate(order):
        result[original_index] = labels_by_rank[rank]
    return result


class OptimizationAlgorithm(ABC):
    id: str
    name: str

    def __init__(self) -> None:
        self.terrain: Optional[TerrainFunction] = None
        self.iterations_used: int = 0

    @abstractmethod
    def initialize(self, x0: tuple[float, float], terrain: TerrainFunction) -> None:
        """Fija el estado interno completo desde el punto de partida x0."""
        raise NotImplementedError

    @abstractmethod
    def get_candidates(self) -> list[Candidate]:
        """Calcula los 5 candidatos reales desde el estado interno actual.
        No modifica ningún estado — es seguro llamarlo repetidamente."""
        raise NotImplementedError

    @abstractmethod
    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        """Ejecuta el paso REAL del algoritmo con el candidato elegido.
        Devuelve el candidato efectivamente aceptado (para Recocido
        Simulado, puede ser la posición ANTERIOR si el dado no favorece
        al candidato peor elegido). Incrementa iterations_used."""
        raise NotImplementedError

    @abstractmethod
    def has_converged(self) -> bool:
        """Criterio de paro matemático real de este algoritmo."""
        raise NotImplementedError

    @abstractmethod
    def get_convergence_indicator(self) -> float:
        """Valor numérico actual del criterio de paro (||grad f||, Delta,
        T, o dispersión del simplex), para mostrar en el HUD."""
        raise NotImplementedError

    @abstractmethod
    def get_current_position(self) -> tuple[float, float]:
        """Dónde está 'parado' el jugador ahora mismo, en coordenadas de
        dominio. Para Nelder-Mead: el mejor vértice del simplex actual."""
        raise NotImplementedError

    @abstractmethod
    def get_current_value(self) -> float:
        """f en get_current_position()."""
        raise NotImplementedError
# IRONEDIT:1783483892:302157c726c062d6f51f53d0748f3f4ddcba0a795894afbb4c76206a9f12a5a6
