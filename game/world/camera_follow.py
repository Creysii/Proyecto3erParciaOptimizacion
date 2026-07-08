"""
CameraFollow: reemplaza a CameraTween con un mecanismo de seguimiento
CONTINUO (no discreto por eventos). En vez de "iniciar una animación de
duración fija hacia un destino fijo", persigue cada frame un objetivo que
el llamador puede recalcular libremente — esto es lo que permite que la
cámara siga al jugador de forma viva mientras camina ENTRE puntos de
decisión, no solo salte de un encuadre estático al siguiente.

Usa suavizado exponencial (1 - e^(-tasa*dt)) en vez de un lerp lineal
ingenuo (current + (target-current)*tasa*dt). La diferencia importa: el
lerp lineal NO es independiente del framerate — a 30 FPS vs 144 FPS
converge a velocidades perceptualmente distintas, y con tasa*dt grande
(frames lentos) puede incluso sobrepasar el objetivo y oscilar. El
suavizado exponencial converge a la misma velocidad percibida sin
importar cuántos frames por segundo esté corriendo el juego.
"""

from __future__ import annotations

import math

from game.world.viewport import ViewportState

DEFAULT_CENTER_LERP_RATE = 6.0  # más alto = sigue al jugador más "pegado"
DEFAULT_SPAN_LERP_RATE = 4.0    # más bajo = el zoom se siente más deliberado


class CameraFollow:
    def __init__(
        self,
        center_lerp_rate: float = DEFAULT_CENTER_LERP_RATE,
        span_lerp_rate: float = DEFAULT_SPAN_LERP_RATE,
    ) -> None:
        self.center_lerp_rate = center_lerp_rate
        self.span_lerp_rate = span_lerp_rate
        self.state = ViewportState(center=(0.0, 0.0), span=10.0)

    def snap_to(self, state: ViewportState) -> None:
        """Teletransporta sin animar — usado al entrar a la sala por
        primera vez, donde no tiene sentido animar 'desde ningún lado'."""
        self.state = state

    def update(self, dt: float, target: ViewportState) -> None:
        cx = self._smooth(self.state.center[0], target.center[0], self.center_lerp_rate, dt)
        cy = self._smooth(self.state.center[1], target.center[1], self.center_lerp_rate, dt)
        span = self._smooth(self.state.span, target.span, self.span_lerp_rate, dt)
        self.state = ViewportState(center=(cx, cy), span=span)

    @staticmethod
    def _smooth(current: float, target: float, rate: float, dt: float) -> float:
        # t se acerca a 1.0 conforme dt crece, pero de forma NO lineal —
        # esto es lo que hace la convergencia independiente del framerate.
        t = 1.0 - math.exp(-rate * dt)
        return current + (target - current) * t
# IRONEDIT:1783483892:41d251c1e4f6ca0ae49503c18df075781bd4cc179976065a7cbdebc8ae33295d
