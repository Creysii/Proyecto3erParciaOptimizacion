"""
ShopVendorInteractable: el vendedor de la tienda. A diferencia de las
puertas/portales (ON_OVERLAP), este es ON_INTERACT — requiere que el
jugador esté en rango Y presione E, para que hablar nunca sea accidental.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from game import config
from game.data.algorithms_config import ALGORITHMS
from game.data.terrain_functions_config import TERRAIN_FUNCTIONS
from game.interactables.base_interactable import Interactable, TriggerMode
from game.ui.shop_overlay import ShopItem, ShopOverlay

if TYPE_CHECKING:
    from game.context import RoomContext

VENDOR_SIZE = 32


class ShopVendorInteractable(Interactable):
    def __init__(self, position: tuple[int, int]) -> None:
        rect = pygame.Rect(0, 0, VENDOR_SIZE, VENDOR_SIZE)
        rect.center = position
        super().__init__(rect, trigger_mode=TriggerMode.ON_INTERACT, prompt_text="Hablar con el vendedor")

    def on_activate(self, context: "RoomContext") -> None:
        def get_items() -> list[ShopItem]:
            items = [
                ShopItem(
                    id=f.id, name=f.name, kind_label="Función", price=f.unlock_cost_coins,
                    unlocked=context.unlocks.is_function_unlocked(f.id),
                )
                for f in TERRAIN_FUNCTIONS if not f.unlocked_by_default
            ]
            items += [
                ShopItem(
                    id=a.id, name=a.name, kind_label="Algoritmo", price=a.unlock_cost_coins,
                    unlocked=context.unlocks.is_algorithm_unlocked(a.id),
                )
                for a in ALGORITHMS if not a.unlocked_by_default
            ]
            # Solo se muestran los ya comprables (no comprados) — una vez
            # adquirido, un ítem desaparece de la lista en la siguiente
            # apertura del overlay (el propio get_items se re-llama cada
            # frame que se dibuja, así que la lista siempre está al día).
            return [item for item in items if not item.unlocked]

        def get_balance() -> int:
            return context.economy.coins

        def attempt_purchase(item: ShopItem) -> bool:
            if not context.economy.spend(item.price):
                return False
            is_function = any(f.id == item.id for f in TERRAIN_FUNCTIONS)
            if is_function:
                context.unlocks.unlock_function(item.id)
            else:
                context.unlocks.unlock_algorithm(item.id)
            return True

        context.overlay_host.open_overlay(ShopOverlay(get_items, get_balance, attempt_purchase))

    def draw_indicator(self, surface: pygame.Surface, context: "RoomContext") -> None:
        pygame.draw.rect(surface, config.COLOR_SHOP_BUILDING, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 230, 120), self.rect, width=2, border_radius=6)
# IRONEDIT:1783512345:9deb48044b30c90e7793b65e395576158119ce13e638272534d35d64803429dd
