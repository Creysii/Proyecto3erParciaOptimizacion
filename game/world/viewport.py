"""
Viewport: traduce entre coordenadas de DOMINIO (las que usa la matemática
real, sin ninguna transformación) y coordenadas de PANTALLA (donde se
dibuja). Es la pieza que hace posible que la posición autoritativa del
jugador dentro de una LevelRoom viva en coordenadas de dominio, mientras
la cámara puede acercarse/alejarse dinámicamente sin que eso afecte en
absoluto la precisión matemática de los cálculos internos.

IdentityViewport formaliza lo que PlazaRoom/ShopRoom ya hacían de forma
implícita (1 unidad de mundo = 1 píxel, sin transformación) — se introduce
aquí para que Room/Player tengan un contrato único y consistente sin
importar en qué contexto se usen.

DecisionViewport separa ESTRICTAMENTE dos responsabilidades que antes
vivían mezcladas en un solo método (frame_points), lo cual causaba que
acercarse a un candidato disparara zoom incorrectamente (el jugador
terminaba formando parte del cálculo de dispersión):

  - compute_target_span(candidate_positions, fallback_bounds): calcula
    SOLO el nivel de zoom, a partir ÚNICAMENTE de la distribución
    espacial de los candidatos. Su firma NO tiene ningún parámetro por
    donde pasar la posición del jugador — no es una promesa de
    comportamiento, es una restricción estructural: sencillamente no
    hay forma de colar esa información aquí por accidente.
  - El CENTRO del encuadre nunca pasa por este viewport en absoluto:
    ExplorationState usa directamente self.player.position como centro,
    manteniendo el seguimiento del jugador completamente separado del
    cálculo de zoom.

Propiedad garantizada: mientras el conjunto de candidatos no cambie
(iteración fija), compute_target_span() devuelve exactamente el mismo
valor sin importar cuántas veces se llame ni qué esté haciendo el
jugador — el span solo cambia cuando cambian los candidatos reales.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame


@dataclass
class ViewportState:
    """Estado completo de un encuadre: centro (en coordenadas de dominio)
    y span (cuánto territorio de dominio cubre el lado del área jugable)."""
    center: tuple[float, float]
    span: float


class Viewport(ABC):
    @abstractmethod
    def domain_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        raise NotImplementedError

    @abstractmethod
    def screen_to_domain(self, point: tuple[int, int]) -> tuple[float, float]:
        raise NotImplementedError

    @abstractmethod
    def y_axis_sign(self) -> float:
        """Multiplicador que convierte 'intención de bajar en pantalla'
        (positivo = tecla S/abajo) en el delta real a sumar a la
        coordenada Y de self.position, sea cual sea el espacio en que
        viva (píxeles en el lobby, dominio en una corrida).

        IdentityViewport: +1.0 (position.y ES la coordenada de pantalla;
        bajar en pantalla = aumentar y directamente).
        DecisionViewport: -1.0 (domain_to_screen invierte Y para lectura
        matemática convencional; bajar en pantalla = DISMINUIR el y de
        dominio, ya que Y de dominio creciente se dibuja hacia ARRIBA)."""
        raise NotImplementedError


class IdentityViewport(Viewport):
    """1 unidad de dominio = 1 píxel de pantalla, sin offset. Usado por
    PlazaRoom/ShopRoom, donde 'mundo' y 'pantalla' siempre fueron lo mismo."""

    def domain_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        return (int(point[0]), int(point[1]))

    def screen_to_domain(self, point: tuple[int, int]) -> tuple[float, float]:
        return (float(point[0]), float(point[1]))

    def y_axis_sign(self) -> float:
        return 1.0


class DecisionViewport(Viewport):
    def __init__(
        self,
        playable_rect: pygame.Rect,
        grid_size: int,
        zoom_margin: float = 1.4,
    ) -> None:
        self.playable_rect = playable_rect
        # grid_size ya NO participa en el cálculo de zoom (ver
        # compute_target_span) — se conserva porque ExplorationState lo
        # sigue usando para la tolerancia de "¿el jugador está parado
        # sobre este candidato?", que sí debe escalar con el zoom actual.
        self.grid_size = grid_size
        # Margen configurable (requisito explícito): cuánto más grande
        # que el diámetro real de los candidatos debe ser el span
        # mostrado, para que no queden pegados al borde de la pantalla.
        # >1.0 siempre (a diferencia del viejo safety_margin, que era <1
        # porque multiplicaba una distancia mínima en vez de un diámetro
        # — significados opuestos, por eso el parámetro se renombró en
        # vez de conservar el nombre con semántica invertida).
        self.zoom_margin = zoom_margin
        self.state = ViewportState(center=(0.0, 0.0), span=10.0)

    def apply_state(self, state: ViewportState) -> None:
        self.state = state

    def domain_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        cx, cy = self.state.center
        span = self.state.span
        rect = self.playable_rect

        # Coordenadas normalizadas dentro de [-0.5, 0.5] del span actual,
        # luego escaladas al tamaño real del área jugable en píxeles.
        norm_x = (point[0] - cx) / span
        norm_y = (point[1] - cy) / span

        screen_x = rect.centerx + norm_x * rect.width
        # Invertimos Y: en el dominio matemático, Y positivo normalmente
        # "sube"; en coordenadas de pantalla, Y positivo "baja". Sin esta
        # inversión, el terreno se vería reflejado verticalmente respecto
        # a como uno esperaría leer una gráfica matemática convencional.
        screen_y = rect.centery - norm_y * rect.height

        return (int(screen_x), int(screen_y))

    def screen_to_domain(self, point: tuple[int, int]) -> tuple[float, float]:
        cx, cy = self.state.center
        span = self.state.span
        rect = self.playable_rect

        norm_x = (point[0] - rect.centerx) / rect.width
        norm_y = -(point[1] - rect.centery) / rect.height

        x = cx + norm_x * span
        y = cy + norm_y * span
        return (x, y)

    def y_axis_sign(self) -> float:
        # domain_to_screen calcula screen_y = centery - norm_y*height, es
        # decir Y de dominio CRECIENTE se dibuja hacia ARRIBA en pantalla
        # (lectura matemática convencional). Por tanto, para bajar en
        # pantalla (intención positiva de S/abajo) hay que DISMINUIR la Y
        # de dominio -> signo negativo, opuesto al de IdentityViewport.
        return -1.0

    def compute_target_span(
        self,
        candidate_positions: list[tuple[float, float]],
        fallback_bounds: tuple[tuple[float, float], tuple[float, float]],
    ) -> float:
        """Calcula ÚNICAMENTE el nivel de zoom objetivo, a partir
        EXCLUSIVAMENTE de la distribución espacial de los candidatos.

        Nótese que esta firma no acepta ni la posición del jugador ni
        ningún otro dato ajeno a los candidatos — es la garantía
        estructural de que el zoom nunca puede reaccionar a dónde está
        parado el jugador.

        Algoritmo: centro del conjunto -> radio máximo (distancia del
        centro al candidato más lejano) -> diámetro -> margen configurable.

        Caso base (menos de 2 candidatos, ej. durante CHOOSING_START antes
        de elegir x0): no hay dispersión que medir, así que se usa el
        tamaño completo del bounds de la función.

        Piso mínimo: si los candidatos están prácticamente superpuestos
        (radio ~ 0 — típico de Nelder-Mead muy cerca de converger), un
        span de ~0 sería una división por cero disfrazada y un zoom
        infinito sin sentido práctico; se usa un span mínimo pequeño en
        su lugar. Esto es DISTINTO del bug original: aquí el radio es
        casi cero porque los candidatos REALES casi coinciden, no porque
        el jugador se haya acercado a uno de ellos.

        Techo: red de seguridad (rara vez activada con esta fórmula,
        a diferencia de la versión anterior) que evita un span
        absurdamente mayor al dominio completo de la función."""
        if len(candidate_positions) < 2:
            (x_min, x_max), (y_min, y_max) = fallback_bounds
            return max(x_max - x_min, y_max - y_min)

        centroid_x = sum(p[0] for p in candidate_positions) / len(candidate_positions)
        centroid_y = sum(p[1] for p in candidate_positions) / len(candidate_positions)

        max_radius = max(
            ((p[0] - centroid_x) ** 2 + (p[1] - centroid_y) ** 2) ** 0.5
            for p in candidate_positions
        )
        if max_radius < 1e-9:
            max_radius = 1e-3

        diameter = 2.0 * max_radius
        span = diameter * self.zoom_margin

        (x_min, x_max), (y_min, y_max) = fallback_bounds
        bounds_span_cap = max(x_max - x_min, y_max - y_min) * 1.1
        span = min(span, bounds_span_cap)

        return span
# IRONEDIT:1783483892:8a4f876d83ab57ad1f856ffca379edd0cea826f4c1c94ed1fadfe2df0eab8502
