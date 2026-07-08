"""
Registro central de algoritmos ("detectores"). Análogo al registro de
funciones objetivo — cualquier código que necesite "el algoritmo con id X"
pasa por aquí.
"""

from __future__ import annotations

from optimization.algorithms.base import OptimizationAlgorithm
from optimization.algorithms.hooke_jeeves import HookeJeeves
from optimization.algorithms.nelder_mead import NelderMead
from optimization.algorithms.newton import Newton
from optimization.algorithms.simulated_annealing import SimulatedAnnealing

ALGORITHM_REGISTRY: dict[str, type[OptimizationAlgorithm]] = {
    "simulated_annealing": SimulatedAnnealing,
    "hooke_jeeves": HookeJeeves,
    "nelder_mead": NelderMead,
    "newton": Newton,
}


def create_algorithm(algorithm_id: str) -> OptimizationAlgorithm:
    if algorithm_id not in ALGORITHM_REGISTRY:
        raise KeyError(
            f"No existe un algoritmo con id '{algorithm_id}'. "
            f"Disponibles: {list(ALGORITHM_REGISTRY.keys())}"
        )
    return ALGORITHM_REGISTRY[algorithm_id]()
# IRONEDIT:1783483892:4ed8408aa081cbe3b5631ae83bff35f0b60449ec665acce1ab6276b49c0ca07e
