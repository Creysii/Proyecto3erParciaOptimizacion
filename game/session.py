"""
GameSession: el objeto que vive por encima de LobbyState y ExplorationState,
dueño único de Economy y Unlocks. Se crea UNA sola vez en main.py y se pasa
por referencia a ambos estados — evita que cada estado tenga su propia
copia de la economía, lo cual haría que las monedas ganadas en una corrida
nunca se reflejaran de vuelta en el lobby.
"""

from __future__ import annotations

from dataclasses import dataclass

from game.progression.economy import Economy
from game.progression.unlocks import Unlocks


@dataclass
class GameSession:
    economy: Economy
    unlocks: Unlocks

    @classmethod
    def new_game(cls) -> "GameSession":
        return cls(economy=Economy(starting_coins=0), unlocks=Unlocks())
# IRONEDIT:1783483891:1235f748fc34e58c88499b80948b75f56a1dd2be97b3d9dd80a8ee929f34dacb
