"""
main() en sí no es fácilmente testeable con pytest (es un loop bloqueante
que corre hasta que el usuario cierra la ventana) — así que este test es
deliberadamente modesto: verifica, leyendo el código fuente, que ESC ya
no se maneja como un caso especial que cierre la aplicación. El
comportamiento real end-to-end (ESC cancela un overlay sin cerrar el
juego) ya está cubierto en tests/test_shop.py
(test_escape_closes_shop_overlay_without_side_effects), que ejercita
exactamente la misma ruta de manejo de eventos que main.py usaría.
"""

from __future__ import annotations

import pathlib


def test_main_no_longer_hijacks_escape_globally():
    source = pathlib.Path(__file__).parent.parent.joinpath("main.py").read_text()
    assert "K_ESCAPE" not in source, (
        "main.py no debería tener ningún caso especial para K_ESCAPE — "
        "antes esto cerraba el juego completo incluso cuando ESC se "
        "presionaba para cancelar un menú, porque el evento nunca "
        "llegaba a game_state_manager."
    )
    assert "game_state_manager.handle_event(event)" in source
# IRONEDIT:1783512345:442a424ad14ee95e9c3e8a954bc9603269d8cf2bd5f0e5ce2139f6d8d7444fd2
