"""
HUD específico de una corrida de exploración. Muestra el indicador de
convergencia CORRECTO según qué algoritmo está activo (‖∇f‖ para Newton,
Delta para Hooke-Jeeves, T para Recocido Simulado, dispersión del simplex
para Nelder-Mead) — el jugador necesita ver ESTE número para poder tomar
la decisión informada de "creo que aquí está el óptimo" que reemplaza un
criterio de paro automático.
"""

from __future__ import annotations

import pygame

from game import config

CONVERGENCE_LABELS = {
    "newton": "‖∇f‖",
    "hooke_jeeves": "Δ",
    "simulated_annealing": "T",
    "nelder_mead": "dispersión",
}


class ExplorationHUD:
    def __init__(self) -> None:
        self._font = pygame.font.SysFont("arial", 20, bold=True)
        self._small_font = pygame.font.SysFont("arial", 15)

    def draw(self, surface: pygame.Surface, function_name: str, algorithm_name: str,
              algorithm_id: str, run) -> None:
        lines = [f"{function_name}  ·  {algorithm_name}"]

        if run.phase.name == "CHOOSING_START":
            lines.append("Camina y presiona ESPACIO para fijar tu punto de partida")
        else:
            f_value = run.trajectory[-1][1]
            indicator = run.get_convergence_indicator()
            label = CONVERGENCE_LABELS.get(algorithm_id, "criterio")
            lines.append(f"f(x) = {f_value:.4f}   {label} = {indicator:.4f}")
            lines.append(f"Iteraciones: {run.algorithm.iterations_used}")

        lines.append("[ESPACIO] activar detector  [V] es el óptimo  [K] vista global")

        padding = 10
        line_surfaces = [self._font.render(lines[0], True, config.COLOR_HUD_TEXT)] + [
            self._small_font.render(line, True, config.COLOR_HUD_TEXT) for line in lines[1:]
        ]
        box_width = max(s.get_width() for s in line_surfaces) + padding * 2
        box_height = sum(s.get_height() + 4 for s in line_surfaces) + padding * 2

        box = pygame.Surface((box_width, box_height))
        box.fill(config.COLOR_HUD_BG)
        box.set_alpha(160)
        surface.blit(box, (16, 16))

        y = 16 + padding
        for line_surface in line_surfaces:
            surface.blit(line_surface, (16 + padding, y))
            y += line_surface.get_height() + 4

    def draw_hovered_candidate_info(self, surface: pygame.Surface, candidate) -> None:
        if candidate is None:
            return
        text = f"f = {candidate.f_value:.4f}  ·  {candidate.quality_label}"
        if candidate.acceptance_probability is not None:
            text += f"  ·  P(aceptar) = {candidate.acceptance_probability:.2f}"
        rendered = self._small_font.render(text, True, (255, 240, 200))
        rect = rendered.get_rect()
        rect.centerx = config.SCREEN_WIDTH // 2
        rect.top = 16
        bg = pygame.Surface((rect.width + 16, rect.height + 10))
        bg.fill((20, 20, 20))
        bg.set_alpha(190)
        surface.blit(bg, (rect.x - 8, rect.y - 5))
        surface.blit(rendered, rect)
# IRONEDIT:1783483891:b1a9363555cdca97395d2400b4b68f98c8982297288c4b15ab04c6014584090f
