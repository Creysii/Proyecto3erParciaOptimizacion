"""
Registro central de funciones objetivo. Cualquier código que necesite
"la función con id X" (game/data/terrain_functions_config.py, el estado
de exploración, los tests) pasa por aquí, en vez de importar cada clase
concreta directamente — así añadir una 5ta función en el futuro es
agregar una línea aquí, sin tocar el código que las consume.
"""

from __future__ import annotations

from optimization.terrain_functions.base import TerrainFunction
from optimization.terrain_functions.himmelblau import Himmelblau
from optimization.terrain_functions.rastrigin import Rastrigin
from optimization.terrain_functions.rosenbrock import Rosenbrock
from optimization.terrain_functions.sphere import Sphere

TERRAIN_FUNCTION_REGISTRY: dict[str, type[TerrainFunction]] = {
    "sphere": Sphere,
    "himmelblau": Himmelblau,
    "rastrigin": Rastrigin,
    "rosenbrock": Rosenbrock,
}


def create_terrain_function(function_id: str) -> TerrainFunction:
    if function_id not in TERRAIN_FUNCTION_REGISTRY:
        raise KeyError(
            f"No existe una función objetivo con id '{function_id}'. "
            f"Disponibles: {list(TERRAIN_FUNCTION_REGISTRY.keys())}"
        )
    return TERRAIN_FUNCTION_REGISTRY[function_id]()
# IRONEDIT:1783483892:70ea863293a164c6a6cc84135e3b2253e1882e9a6ecf7927850348433b70ca7b
