"""
Catálogo de funciones objetivo disponibles en el lobby. Renombrado desde
levels_config.py/LevelConfig — con la reinterpretación acordada, los
portales del lobby representan FUNCIONES OBJETIVO, no algoritmos.

Deliberadamente es solo datos (dataclass + lista), sin lógica. PlazaRoom
itera esta lista para crear un LevelPortalInteractable por cada entrada.

El campo unlock_requires_key del prototipo original se elimina: las
llaves de función son desbloqueos PERMANENTES comprados con monedas, no
objetos consumibles — se representan enteramente con unlock_cost_coins.
"""

from __future__ import annotations

from dataclasses import dataclass

UNLOCK_COST = 100  # PRECIO TEMPORAL — se ajustará junto con el sistema de economía completo


@dataclass(frozen=True)
class TerrainFunctionConfig:
    id: str
    name: str
    portal_position: tuple[int, int]  # centro del portal, coords de mundo (PlazaRoom)
    unlocked_by_default: bool
    unlock_cost_coins: int


TERRAIN_FUNCTIONS: list[TerrainFunctionConfig] = [
    TerrainFunctionConfig(
        id="sphere",
        name="Sphere",
        portal_position=(760, 160),
        unlocked_by_default=True,
        unlock_cost_coins=0,
    ),
    TerrainFunctionConfig(
        id="himmelblau",
        name="Himmelblau",
        portal_position=(860, 280),
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
    TerrainFunctionConfig(
        id="rastrigin",
        name="Rastrigin",
        portal_position=(760, 400),
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
    TerrainFunctionConfig(
        id="rosenbrock",
        name="Rosenbrock",
        portal_position=(660, 280),
        unlocked_by_default=False,
        unlock_cost_coins=UNLOCK_COST,
    ),
]


def get_terrain_function_config(function_id: str) -> TerrainFunctionConfig:
    for func in TERRAIN_FUNCTIONS:
        if func.id == function_id:
            return func
    raise KeyError(f"No existe una función objetivo con id '{function_id}'")
# IRONEDIT:1783512345:9c0894c72cc402c6221099b4177b538ded5b4dab3c0bb779cd18274304462530
