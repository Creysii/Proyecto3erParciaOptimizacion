"""
Tests del flujo de compra en la tienda (ShopVendorInteractable + ShopOverlay),
sobre LobbyState real — verifican que la compra deduce monedas, desbloquea
el ítem correcto, y maneja correctamente fondos insuficientes y compras
duplicadas.
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from game.session import GameSession
from game.state_manager import GameStateManager
from game.world.rooms.shop_room import VENDOR_POSITION


@pytest.fixture(autouse=True, scope="module")
def _pygame_headless():
    pygame.init()
    pygame.display.set_mode((960, 640))
    yield
    pygame.quit()


def _enter_shop_and_talk_to_vendor(session):
    gsm = GameStateManager(session)
    lobby = gsm.current_state
    from game.world.rooms.plaza_room import SHOP_DOOR_RECT

    lobby.player.set_position(SHOP_DOOR_RECT.center)
    lobby.update(1 / 60)
    for _ in range(40):
        lobby.update(1 / 60)

    lobby.player.set_position(VENDOR_POSITION)
    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    lobby.update(1 / 60)
    return lobby


def test_shop_lists_all_locked_items_with_temporary_price():
    session = GameSession.new_game()
    lobby = _enter_shop_and_talk_to_vendor(session)
    shop = lobby.active_overlay
    items = shop.get_items()

    assert len(items) == 6  # 3 funciones + 3 algoritmos, todos bloqueados por defecto
    assert all(item.price == 100 for item in items)
    assert all(not item.unlocked for item in items)


def test_purchase_deducts_coins_and_unlocks_item():
    session = GameSession.new_game()
    session.economy.add(100)
    lobby = _enter_shop_and_talk_to_vendor(session)
    shop = lobby.active_overlay

    target_item = shop.get_items()[0]
    assert not session.unlocks.is_function_unlocked(target_item.id) and \
           not session.unlocks.is_algorithm_unlocked(target_item.id)

    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

    assert session.economy.coins == 0
    is_function = target_item.kind_label == "Función"
    if is_function:
        assert session.unlocks.is_function_unlocked(target_item.id)
    else:
        assert session.unlocks.is_algorithm_unlocked(target_item.id)

    # El ítem ya no debe aparecer en la lista de compra.
    remaining_ids = [i.id for i in shop.get_items()]
    assert target_item.id not in remaining_ids


def test_purchase_fails_gracefully_with_insufficient_funds():
    session = GameSession.new_game()
    session.economy.add(50)  # no alcanza para 100
    lobby = _enter_shop_and_talk_to_vendor(session)
    shop = lobby.active_overlay

    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

    assert session.economy.coins == 50  # nada se cobró
    assert "alcanzan" in shop._feedback_message.lower()


def test_escape_closes_shop_overlay_without_side_effects():
    session = GameSession.new_game()
    session.economy.add(500)
    lobby = _enter_shop_and_talk_to_vendor(session)
    assert lobby.active_overlay is not None

    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    lobby.update(1 / 60)

    assert lobby.active_overlay is None
    assert session.economy.coins == 500  # nada se compró
# IRONEDIT:1783512345:8ef2724cc56c797e8e918793b9d2890783cf395a15349cf67e575039b88daa6b
