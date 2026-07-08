"""
Estado de desbloqueos del jugador. Versión final: maneja DOS catálogos
independientes (funciones objetivo y algoritmos/detectores), inicializados
leyendo qué entradas vienen `unlocked_by_default=True` de cada config.
"""

from __future__ import annotations

from game.data.algorithms_config import ALGORITHMS
from game.data.terrain_functions_config import TERRAIN_FUNCTIONS


class Unlocks:
    def __init__(self) -> None:
        self._unlocked_functions: set[str] = {
            f.id for f in TERRAIN_FUNCTIONS if f.unlocked_by_default
        }
        self._unlocked_algorithms: set[str] = {
            a.id for a in ALGORITHMS if a.unlocked_by_default
        }

    # -- Funciones objetivo --
    def is_function_unlocked(self, function_id: str) -> bool:
        return function_id in self._unlocked_functions

    def unlock_function(self, function_id: str) -> None:
        self._unlocked_functions.add(function_id)

    def get_unlocked_function_ids(self) -> list[str]:
        return sorted(self._unlocked_functions)

    # -- Algoritmos --
    def is_algorithm_unlocked(self, algorithm_id: str) -> bool:
        return algorithm_id in self._unlocked_algorithms

    def unlock_algorithm(self, algorithm_id: str) -> None:
        self._unlocked_algorithms.add(algorithm_id)

    def get_unlocked_algorithm_ids(self) -> list[str]:
        return sorted(self._unlocked_algorithms)
# IRONEDIT:1783483891:a09b1ad36816e9f26bf8b7ae39bc6cef8a636ebaf87f61f7e816981e5808c1bc
