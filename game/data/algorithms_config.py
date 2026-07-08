"""
Catálogo de algoritmos ("detectores") disponibles. Independiente del
catálogo de funciones — el jugador elige combinación función+algoritmo
libremente entre lo que tenga desbloqueado de cada catálogo por separado.

Recocido Simulado viene desbloqueado por defecto: es el más simple de
explicar en los primeros segundos ("genero un vecino, si es mejor lo
acepto, si es peor tiro un dado").
"""

from __future__ import annotations

from dataclasses import dataclass

from game.data.terrain_functions_config import UNLOCK_COST


@dataclass(frozen=True)
class AlgorithmConfig:
    id: str
    name: str
    unlocked_by_default: bool
    unlock_cost_coins: int


ALGORITHMS: list[AlgorithmConfig] = [
    AlgorithmConfig(
        id="simulated_annealing",
        name="Recocido Simulado",
        unlocked_by_default=True,
        unlock_cost_coins=0,
    ),
    AlgorithmConfig(
        id="hooke_jeeves",
        name="Hooke-Jeeves",
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
    AlgorithmConfig(
        id="nelder_mead",
        name="Nelder-Mead",
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
    AlgorithmConfig(
        id="newton",
        name="Newton",
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
]


def get_algorithm_config(algorithm_id: str) -> AlgorithmConfig:
    for algo in ALGORITHMS:
        if algo.id == algorithm_id:
            return algo
    raise KeyError(f"No existe un algoritmo con id '{algorithm_id}'")
# IRONEDIT:1783511592:5e9b33e147ca37286188c54a2346fccd38e9b39b9157b5b7a84d119f31fb6e15
