"""
Tabla de multiplicadores de recompensa por combinación (algoritmo, función).
Todos en 1.0 por ahora — placeholder neutro, ajustable tras el primer
playtesting real, tal como se acordó explícitamente con el equipo.
"""

from __future__ import annotations

from game.data.algorithms_config import ALGORITHMS
from game.data.terrain_functions_config import TERRAIN_FUNCTIONS

SCORING_MULTIPLIERS: dict[tuple[str, str], float] = {
    (algo.id, func.id): 1.0 for algo in ALGORITHMS for func in TERRAIN_FUNCTIONS
}
# IRONEDIT:1783511592:6e3d2678571e0f954880189d2c397f6eecb9e8f3d1e9290953203e8dbbc9e298
