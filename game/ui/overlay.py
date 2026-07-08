"""
Overlay: un elemento de UI que pausa la room activa mientras está abierto,
captura su propio input, y se dibuja encima de todo lo demás. Usado tanto
por DetectorSelectMenu (elegir algoritmo antes de entrar a un nivel) como,
a futuro, por el overlay de compra de la tienda — ambos comparten este
mismo patrón de "pausar y tomar control temporalmente".
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pygame


class Overlay(ABC):
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def update(self, dt: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_done(self) -> bool:
        """True cuando el overlay debe cerrarse y devolver el control a la room."""
        raise NotImplementedError
# IRONEDIT:1783483891:e07aa8f33f2452af2dc845555931232d33d7ff6ebd6cd678797c914896f1d717
