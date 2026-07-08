"""
Economía del jugador. Versión mínima en memoria — sin persistencia todavía
(eso llegará con save_system.py más adelante). Lo importante en esta
entrega es que la tubería de datos ya exista: el HUD lee coins de aquí,
y a futuro scoring.py escribirá aquí al terminar una expedición.
"""

from __future__ import annotations


class Economy:
    def __init__(self, starting_coins: int = 0) -> None:
        self.coins = starting_coins

    def add(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("add() no acepta cantidades negativas; usa spend().")
        self.coins += amount

    def spend(self, amount: int) -> bool:
        """Intenta gastar `amount` monedas. Devuelve False si no alcanza,
        sin modificar el saldo."""
        if amount < 0:
            raise ValueError("spend() no acepta cantidades negativas.")
        if self.coins < amount:
            return False
        self.coins -= amount
        return True
# IRONEDIT:1783483891:15f6b339dfc8c7ae875949e250fe21811eecd64107ca82526b8894541e09943a
