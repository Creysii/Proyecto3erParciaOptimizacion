"""
Efectos visuales específicos por algoritmo — cada uno traduce visualmente
la forma real en que ese algoritmo explora, según la tabla de diseño
acordada. Cada función recibe (surface, viewport, algorithm, candidates)
y no necesita saber nada de ExplorationState; ExplorationState decide
cuál llamar según isinstance(algorithm, ...).
"""

from __future__ import annotations

import math

import pygame

from game.algorithms_visual_config import (
    COLOR_ELLIPSE,
    COLOR_NEWTON_ARROW,
    COLOR_RADAR_LINE,
    COLOR_SA_CLOUD,
    COLOR_SIMPLEX_EDGE,
)
from game.world.viewport import Viewport
from optimization.algorithms.base import Candidate
from optimization.algorithms.hooke_jeeves import HookeJeeves
from optimization.algorithms.nelder_mead import NelderMead
from optimization.algorithms.newton import Newton
from optimization.algorithms.simulated_annealing import SimulatedAnnealing


def draw_simulated_annealing_effect(
    surface: pygame.Surface, viewport: Viewport, algorithm: SimulatedAnnealing,
    candidates: list[Candidate],
) -> None:
    """Nube de puntos tenues (los vecinos candidatos) alrededor del
    jugador — su radio real se encoge junto con la temperatura."""
    center_screen = viewport.domain_to_screen(algorithm.get_current_position())
    radius_domain = algorithm.get_neighbor_radius()
    edge_screen = viewport.domain_to_screen(
        (algorithm.get_current_position()[0] + radius_domain, algorithm.get_current_position()[1])
    )
    radius_px = abs(edge_screen[0] - center_screen[0])
    radius_px = max(4, min(radius_px, 400))

    ring_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(ring_surface, (*COLOR_SA_CLOUD, 90), center_screen, int(radius_px), width=2)
    surface.blit(ring_surface, (0, 0))


def draw_hooke_jeeves_effect(
    surface: pygame.Surface, viewport: Viewport, algorithm: HookeJeeves,
    candidates: list[Candidate],
) -> None:
    """Cuatro líneas cortas disparadas hacia cada eje cardinal (radar de
    cuatro direcciones) — su longitud se encoge cuando Delta se reduce."""
    origin_screen = viewport.domain_to_screen(algorithm.get_current_position())
    axis_labels = {"+delta_x", "-delta_x", "+delta_y", "-delta_y"}
    for candidate in candidates:
        if candidate.operation_label in axis_labels:
            target_screen = viewport.domain_to_screen(candidate.position)
            pygame.draw.line(surface, COLOR_RADAR_LINE, origin_screen, target_screen, width=2)


def draw_nelder_mead_effect(
    surface: pygame.Surface, viewport: Viewport, algorithm: NelderMead,
    candidates: list[Candidate],
) -> None:
    """El triángulo del simplex, dibujado permanentemente en el suelo."""
    positions = algorithm.get_simplex_positions()
    screen_points = [viewport.domain_to_screen(p) for p in positions]
    pygame.draw.polygon(surface, COLOR_SIMPLEX_EDGE, screen_points, width=2)
    for point in screen_points:
        pygame.draw.circle(surface, COLOR_SIMPLEX_EDGE, point, 4)


def draw_newton_effect(
    surface: pygame.Surface, viewport: Viewport, algorithm: Newton,
    candidates: list[Candidate],
) -> None:
    """Flecha larga (dirección de Newton) con marcas de line search, más
    una elipse tenue representando la aproximación cuadrática local real
    (ejes = eigenvectores de H, escala de cada semieje ~ 1/sqrt(eigenvalor))."""
    origin_domain = algorithm.get_current_position()
    origin_screen = viewport.domain_to_screen(origin_domain)

    # Flecha: desde el origen hasta el candidato de mayor alpha (el más lejano
    # a lo largo de la dirección real de Newton).
    if candidates:
        farthest = max(
            candidates,
            key=lambda c: (c.position[0] - origin_domain[0]) ** 2
            + (c.position[1] - origin_domain[1]) ** 2,
        )
        farthest_screen = viewport.domain_to_screen(farthest.position)
        pygame.draw.line(surface, COLOR_NEWTON_ARROW, origin_screen, farthest_screen, width=3)
        # Marcas de line search: un punto pequeño en cada uno de los 5 alphas.
        for candidate in candidates:
            p = viewport.domain_to_screen(candidate.position)
            pygame.draw.circle(surface, COLOR_NEWTON_ARROW, p, 3)

    # Elipse de la aproximación cuadrática local (Hessiana REAL, sin
    # estabilizar, para mostrar honestamente cuándo se vuelve patológica).
    eigenvalues, eigenvectors = algorithm.get_local_quadratic_model()
    _draw_curvature_ellipse(surface, viewport, origin_screen, eigenvalues, eigenvectors)


def _draw_curvature_ellipse(surface, viewport, center_screen, eigenvalues, eigenvectors) -> None:
    # Semieje proporcional a 1/sqrt(|eigenvalor|); escala visual arbitraria
    # (VISUAL_SCALE) solo para que el tamaño sea legible en pantalla, con
    # un piso/techo en píxeles para que un eigenvalor casi-cero (Hessiana
    # casi singular) no produzca una elipse literalmente infinita.
    VISUAL_SCALE = 40.0
    MIN_PX, MAX_PX = 15, 250

    safe_eigs = [max(abs(e), 1e-3) for e in eigenvalues]
    semi_axes_px = [
        max(MIN_PX, min(MAX_PX, VISUAL_SCALE / math.sqrt(e))) for e in safe_eigs
    ]

    angle = math.atan2(eigenvectors[1, 0], eigenvectors[0, 0])

    ellipse_surface_size = int(max(semi_axes_px) * 2.2)
    ellipse_surface = pygame.Surface((ellipse_surface_size, ellipse_surface_size), pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, semi_axes_px[0] * 2, semi_axes_px[1] * 2)
    rect.center = (ellipse_surface_size // 2, ellipse_surface_size // 2)
    pygame.draw.ellipse(ellipse_surface, (*COLOR_ELLIPSE, 80), rect, width=2)

    rotated = pygame.transform.rotate(ellipse_surface, -math.degrees(angle))
    rotated_rect = rotated.get_rect(center=center_screen)
    surface.blit(rotated, rotated_rect)


def draw_algorithm_effect(surface, viewport, algorithm, candidates) -> None:
    """Despacha al efecto correcto según el tipo real del algoritmo — el
    único lugar que necesita conocer las 4 clases concretas."""
    if isinstance(algorithm, SimulatedAnnealing):
        draw_simulated_annealing_effect(surface, viewport, algorithm, candidates)
    elif isinstance(algorithm, HookeJeeves):
        draw_hooke_jeeves_effect(surface, viewport, algorithm, candidates)
    elif isinstance(algorithm, NelderMead):
        draw_nelder_mead_effect(surface, viewport, algorithm, candidates)
    elif isinstance(algorithm, Newton):
        draw_newton_effect(surface, viewport, algorithm, candidates)
# IRONEDIT:1783483891:2e125d63f69af167a7971cc17640c01c9cc5439741da7e2e96186184fc73039d
