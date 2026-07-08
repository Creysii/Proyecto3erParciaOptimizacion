"""
Clase base para una función objetivo (el "terreno" que el jugador explora).

Deliberadamente NO depende de pygame ni de nada del motor de juego: es
matemática pura, testeable con pytest sin abrir ninguna ventana. Cada
función concreta implementa evaluate/gradient/hessian de forma ANALÍTICA
(derivada a mano), nunca numérica por diferencias finitas — esa fue una
decisión de fidelidad explícita, no un descuido.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TerrainFunction(ABC):
    id: str
    name: str
    # ((x_min, x_max), (y_min, y_max)) — convención de encuadre inicial,
    # NO una restricción matemática real (la función está definida en R^2
    # completo; el algoritmo puede legítimamente proponer puntos fuera de
    # este rectángulo).
    bounds: tuple[tuple[float, float], tuple[float, float]]
    global_optimum_position: tuple[float, float]
    global_optimum_value: float

    @abstractmethod
    def evaluate(self, x: float, y: float) -> float:
        """f(x, y), con precisión de punto flotante completa. Nunca se
        suaviza ni se cuantiza."""
        raise NotImplementedError

    @abstractmethod
    def gradient(self, x: float, y: float) -> tuple[float, float]:
        """(df/dx, df/dy), derivado analíticamente."""
        raise NotImplementedError

    @abstractmethod
    def hessian(self, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]]:
        """[[d2f/dx2, d2f/dxdy], [d2f/dydx, d2f/dy2]], derivado analíticamente."""
        raise NotImplementedError

    def gradient_norm(self, x: float, y: float) -> float:
        """Utilidad compartida: ||grad f||, usada por varios criterios de
        paro (Newton en particular, pero útil como indicador para todos)."""
        gx, gy = self.gradient(x, y)
        return (gx**2 + gy**2) ** 0.5
# IRONEDIT:1783483892:996080c68985b6773a55a8b041c51d4201533650089d108e04d38b4fb948f39a
