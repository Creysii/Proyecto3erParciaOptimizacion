"""
ExplorationState: el segundo gran estado del juego (junto a LobbyState),
alternado por GameStateManager. Envuelve OptimizationRun (el motor puro,
sin pygame) con todo lo visual: DecisionViewport + CameraFollow (cámara
de seguimiento continuo), input del jugador, HUD, y los efectos visuales
por algoritmo.

Es una "sala sin salida": la única forma de terminar la corrida es el
botón de victoria (tecla V), disponible desde que se elige x0. No hay ESC
para salir anticipadamente (más allá del ESC global de main.py que cierra
todo el programa).

Cámara (revisión 3 — separación ESTRICTA entre seguimiento y zoom):
CameraFollow persigue CADA FRAME un ViewportState objetivo recalculado en
_compute_camera_target(). Ese objetivo se arma combinando dos cálculos que
NUNCA se mezclan entre sí:

  - CENTRO: siempre self.player.position, directamente. La cámara sigue
    al jugador explorando la sala — nada más.
  - SPAN: siempre viewport.compute_target_span(candidate_positions, ...),
    cuya firma ni siquiera acepta la posición del jugador como parámetro.
    El zoom depende ÚNICAMENTE de la dispersión real de los candidatos
    (centro del conjunto -> radio máximo -> diámetro -> margen
    configurable en config.DECISION_ZOOM_MARGIN), nunca de un cronómetro
    artificial de iteraciones ni de dónde esté parado el jugador.

Garantía resultante: mientras el conjunto de candidatos no cambie (el
jugador simplemente camina entre ellos, sin confirmar ninguno), el span
objetivo es EXACTAMENTE el mismo en cada frame — acercarse a un candidato
nunca dispara zoom por sí solo. (Revisión anterior: el jugador se incluía
en el mismo conjunto de puntos usado para calcular dispersión, lo cual
hacía que acercarse a un candidato se interpretara como "los candidatos
se juntaron", produciendo zoom incorrecto y una fórmula además basada en
distancia MÍNIMA entre pares — muy sensible a un solo par atípico. Ambos
problemas quedaron resueltos con esta separación.)

Modo observador global (tecla K): aleja la cámara para mostrar toda la
región relevante (bounds ∪ trayectoria recorrida ∪ candidatos activos),
centrada en la caja envolvente real — no en un (0,0) fijo, que sería
incorrecto para funciones como Rosenbrock cuyo bounds no está centrado en
el origen. Cualquier acción (activar detector o declarar victoria)
desactiva automáticamente el modo observador, para que el jugador siempre
actúe desde la vista de seguimiento normal.
"""

from __future__ import annotations

from typing import Callable, Optional

import pygame

from game import config
from game.data.algorithms_config import get_algorithm_config
from game.data.terrain_functions_config import get_terrain_function_config
from game.entities.player import Player
from game.rendering.algorithm_effects import draw_algorithm_effect
from game.session import GameSession
from game.ui.exploration_hud import ExplorationHUD
from game.ui.message_queue import MessageQueue
from game.world.camera_follow import CameraFollow
from game.world.viewport import DecisionViewport, ViewportState
from optimization.algorithms.base import Candidate
from optimization.algorithms.registry import create_algorithm
from optimization.level_room import OptimizationRun, RunPhase
from optimization.scoring.run_result import PlaceholderRewardStrategy
from optimization.terrain_functions.registry import create_terrain_function

RESULT_DISPLAY_SECONDS = 4.0
WALL_THICKNESS = 24


def _build_playable_boundary_walls(playable_rect: pygame.Rect) -> list[pygame.Rect]:
    """Cuatro rectángulos de colisión justo fuera del área jugable —
    el 'borde de la excavación' del que no se puede salir caminando."""
    t = WALL_THICKNESS
    return [
        pygame.Rect(playable_rect.left - t, playable_rect.top - t, playable_rect.width + 2 * t, t),
        pygame.Rect(playable_rect.left - t, playable_rect.bottom, playable_rect.width + 2 * t, t),
        pygame.Rect(playable_rect.left - t, playable_rect.top - t, t, playable_rect.height + 2 * t),
        pygame.Rect(playable_rect.right, playable_rect.top - t, t, playable_rect.height + 2 * t),
    ]


class ExplorationState:
    def __init__(
        self,
        function_id: str,
        algorithm_id: str,
        session: GameSession,
        on_finish: Callable[[], None],
        scoring_multipliers: Optional[dict[tuple[str, str], float]] = None,
    ) -> None:
        if scoring_multipliers is None:
            from game.data.scoring_config import SCORING_MULTIPLIERS
            scoring_multipliers = SCORING_MULTIPLIERS

        self.terrain = create_terrain_function(function_id)
        self.algorithm = create_algorithm(algorithm_id)
        self.function_name = get_terrain_function_config(function_id).name
        self.algorithm_name = get_algorithm_config(algorithm_id).name
        self.algorithm_id = algorithm_id

        self.run = OptimizationRun(self.terrain, self.algorithm, max_iterations=config.MAX_ITERATIONS_SAFETY)
        self.session = session
        self.on_finish = on_finish
        self._reward_strategy = PlaceholderRewardStrategy(scoring_multipliers)

        playable_rect = pygame.Rect(
            config.PLAYABLE_RECT_TOPLEFT[0], config.PLAYABLE_RECT_TOPLEFT[1],
            config.PLAYABLE_RECT_SIZE, config.PLAYABLE_RECT_SIZE,
        )
        self.playable_rect = playable_rect
        self.collision_rects = _build_playable_boundary_walls(playable_rect)

        self.viewport = DecisionViewport(
            playable_rect, config.DECISION_GRID_SIZE, zoom_margin=config.DECISION_ZOOM_MARGIN
        )
        initial_span = self.viewport.compute_target_span([], fallback_bounds=self.terrain.bounds)
        (x_min, x_max), (y_min, y_max) = self.terrain.bounds
        initial_center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
        self.viewport.apply_state(ViewportState(center=initial_center, span=initial_span))

        self.camera_follow = CameraFollow()
        self.camera_follow.snap_to(self.viewport.state)

        # Modo observador global (tecla K) — ver docstring del módulo.
        self.show_global_map = False

        (x_min, x_max), (y_min, y_max) = self.terrain.bounds
        start_pos = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
        self.player = Player(start_pos=start_pos)
        # Velocidad inicial coherente con el span de arranque; se
        # recalcula cada frame en update() para seguir el zoom actual.
        self.player.speed = config.EXPLORATION_SPEED_SPAN_FRACTION * self.viewport.state.span

        self.hud = ExplorationHUD()
        self.hud_messages = MessageQueue()

        self._finish_timer: Optional[float] = None

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self._finish_timer is not None:
            return  # ignorar input mientras se muestra el resultado final

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._activate_detector()
            elif event.key == pygame.K_v:
                self._declare_victory()
            elif event.key == pygame.K_k:
                self.show_global_map = not self.show_global_map

    def _activate_detector(self) -> None:
        self.show_global_map = False  # cualquier acción real vuelve a la vista de seguimiento

        if self.run.phase == RunPhase.CHOOSING_START:
            x0 = (self.player.position.x, self.player.position.y)
            self.run.choose_start(x0)
            f0 = self.run.trajectory[0][1]
            self.hud_messages.show(f"Punto inicial fijado — f(x0) = {f0:.4f}", duration=2.5)
            return

        if self.run.phase == RunPhase.SHOWING_CANDIDATES:
            hovered = self._get_hovered_candidate()
            if hovered is None:
                self.hud_messages.show("Párate sobre un candidato iluminado para confirmarlo", 2.0)
                return

            accepted = self.run.confirm_candidate(hovered)
            self.player.set_position(accepted.position)
            self.hud_messages.show(self._build_move_message(hovered, accepted), duration=3.0)

            if self.run.is_finished():
                self._finish_and_reward()

    def _declare_victory(self) -> None:
        if self.run.phase == RunPhase.CHOOSING_START:
            # Mismo error que antes producía un IndexError críptico en
            # OptimizationRun — aquí se intercepta ANTES de llegar a esa
            # capa, con un mensaje que le explica al jugador qué hacer.
            self.hud_messages.show("Primero elige tu punto de partida con ESPACIO", 2.5)
            return
        if self.run.is_finished():
            return

        self.show_global_map = False
        self.run.declare_victory()
        self._finish_and_reward()

    def _build_move_message(self, chosen: Candidate, accepted: Candidate) -> str:
        if accepted.quality_label == "rechazado":
            return (
                f"Elegiste {chosen.operation_label} ({chosen.quality_label}), "
                f"pero el detector RECHAZÓ el paso (dado desfavorable)"
            )
        return f"Movimiento: {accepted.operation_label} — {accepted.quality_label}"

    def _finish_and_reward(self) -> None:
        result = self.run.result
        assert result is not None
        reward = self._reward_strategy.compute(result)
        self.session.economy.add(reward)

        progress_pct = int(round(result.relative_progress() * 100))
        reason = "Decidiste parar aquí" if result.ended_by_player else "Límite de iteraciones alcanzado"
        message = (
            f"{reason} — progreso relativo {progress_pct}% "
            f"({result.iterations_used} iteraciones) — +{reward} monedas"
        )
        self.hud_messages.show(message, duration=RESULT_DISPLAY_SECONDS)
        self._finish_timer = RESULT_DISPLAY_SECONDS

    # ------------------------------------------------------------------
    # Cámara — objetivo recalculado cada frame, perseguido continuamente
    # ------------------------------------------------------------------
    def _compute_camera_target(self) -> ViewportState:
        if self.show_global_map:
            return self._compute_overview_target()

        if self.run.phase == RunPhase.CHOOSING_START:
            # Cámara FIJA en el centro del dominio completo — el jugador
            # recorre libremente todo el "mapa" para elegir x0. Si la
            # cámara persiguiera al jugador aquí (como en SHOWING_CANDIDATES),
            # el seguimiento tan ceñido (center_lerp_rate alto) cancelaría
            # casi todo el desplazamiento visible en pantalla, dando la
            # sensación de que el jugador no se mueve — aunque su posición
            # de dominio sí cambie. Con la cámara fija, caminar se nota de
            # verdad contra un fondo estable, y las paredes de colisión de
            # la sala vuelven a tener sentido real (alcanzables).
            (x_min, x_max), (y_min, y_max) = self.terrain.bounds
            fixed_center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
            span = self.viewport.compute_target_span([], fallback_bounds=self.terrain.bounds)
            return ViewportState(center=fixed_center, span=span)

        # SHOWING_CANDIDATES: aquí sí, la cámara sigue activamente al
        # jugador mientras explora entre los candidatos ya generados.
        center = (self.player.position.x, self.player.position.y)
        candidate_positions = [c.position for c in self.run.current_candidates]
        span = self.viewport.compute_target_span(candidate_positions, fallback_bounds=self.terrain.bounds)
        return ViewportState(center=center, span=span)

    def _compute_overview_target(self) -> ViewportState:
        (x_min, x_max), (y_min, y_max) = self.terrain.bounds
        xs = [x_min, x_max]
        ys = [y_min, y_max]

        for position, _ in self.run.trajectory:
            xs.append(position[0])
            ys.append(position[1])
        for candidate in self.run.current_candidates:
            xs.append(candidate.position[0])
            ys.append(candidate.position[1])
        # Incluir los óptimos globales garantiza que, al finalizar la
        # partida (que reutiliza este mismo encuadre), el marcador del
        # óptimo real quede siempre visible junto con el resultado del
        # jugador, sin importar qué tan lejos haya quedado uno del otro.
        all_optima = [self.terrain.global_optimum_position, *self.terrain.additional_global_optima]
        for optimum_position in all_optima:
            xs.append(optimum_position[0])
            ys.append(optimum_position[1])

        center = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
        span = max(max(xs) - min(xs), max(ys) - min(ys)) * config.OVERVIEW_MARGIN_FACTOR
        span = max(span, 1e-3)
        return ViewportState(center=center, span=span)

    def _get_hovered_candidate(self) -> Optional[Candidate]:
        tolerance = (self.viewport.state.span / self.viewport.grid_size) * 0.9
        px, py = self.player.position.x, self.player.position.y
        best: Optional[Candidate] = None
        best_dist = tolerance
        for candidate in self.run.current_candidates:
            cx, cy = candidate.position
            dist = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
            if dist < best_dist:
                best = candidate
                best_dist = dist
        return best

    # ------------------------------------------------------------------
    # Ciclo por frame
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.hud_messages.update(dt)

        if self._finish_timer is not None:
            self._finish_timer -= dt
            # La cámara se abre para mostrar el resultado final junto al
            # marcador del óptimo global — sin esto, la comparación visual
            # podría quedar fuera de pantalla si el algoritmo convergió
            # lejos del óptimo real (ej. atrapado en un mínimo local).
            self.camera_follow.update(dt, self._compute_overview_target())
            self.viewport.apply_state(self.camera_follow.state)
            if self._finish_timer <= 0:
                self.on_finish()
            return

        keys = pygame.key.get_pressed()
        # Velocidad como fracción del span VISIBLE actual — no del span
        # objetivo (que podría estar a mitad de una transición de zoom).
        # Esto es lo que hace que el movimiento se sienta uniforme sin
        # importar qué tan acercada o alejada esté la cámara en este momento.
        self.player.speed = config.EXPLORATION_SPEED_SPAN_FRACTION * self.viewport.state.span
        self.player.handle_input(keys)
        self.player.try_move(dt, self.collision_rects, self.viewport)

        target = self._compute_camera_target()
        self.camera_follow.update(dt, target)
        self.viewport.apply_state(self.camera_follow.state)

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((25, 22, 20))
        pygame.draw.rect(surface, config.COLOR_PLAYABLE_BG, self.playable_rect)
        pygame.draw.rect(surface, config.COLOR_PLAYABLE_BORDER, self.playable_rect, width=3)

        self._draw_trajectory(surface)

        hovered = None
        if self.run.phase == RunPhase.SHOWING_CANDIDATES:
            draw_algorithm_effect(surface, self.viewport, self.algorithm, self.run.current_candidates)
            self._draw_candidates(surface)
            if not self.show_global_map:
                hovered = self._get_hovered_candidate()

        self.player.draw(surface, self.viewport)

        if self._finish_timer is not None:
            self._draw_global_optimum_markers(surface)

        self.hud.draw(surface, self.function_name, self.algorithm_name, self.algorithm_id, self.run)
        self.hud.draw_hovered_candidate_info(surface, hovered)
        if self.show_global_map:
            self._draw_overview_indicator(surface)
        self.hud_messages.draw(surface)

    def _draw_trajectory(self, surface: pygame.Surface) -> None:
        if len(self.run.trajectory) < 2:
            return
        points = [self.viewport.domain_to_screen(p) for p, _ in self.run.trajectory]
        pygame.draw.lines(surface, config.COLOR_TRAJECTORY_LINE, False, points, width=2)
        for p in points:
            pygame.draw.circle(surface, config.COLOR_TRAJECTORY_LINE, p, 3)

    def _draw_candidates(self, surface: pygame.Surface) -> None:
        color_by_label = {
            "brillante": config.COLOR_CANDIDATE_BRILLIANT,
            "buena": config.COLOR_CANDIDATE_GOOD,
            "neutral": config.COLOR_CANDIDATE_NEUTRAL,
        }
        for candidate in self.run.current_candidates:
            screen_pos = self.viewport.domain_to_screen(candidate.position)
            color = color_by_label.get(candidate.quality_label, config.COLOR_CANDIDATE_NEUTRAL)
            pygame.draw.circle(surface, color, screen_pos, 10)
            pygame.draw.circle(surface, (0, 0, 0), screen_pos, 10, width=2)

    def _draw_global_optimum_markers(self, surface: pygame.Surface) -> None:
        """Marca la posición REAL del óptimo global al finalizar la
        corrida, para comparar visualmente contra dónde terminó el
        jugador. Si la función tiene varios óptimos globales igualmente
        válidos (ej. Himmelblau), se marcan TODOS — sin necesitar ninguna
        lógica especial por función aquí, gracias a additional_global_optima."""
        all_optima = [self.terrain.global_optimum_position, *self.terrain.additional_global_optima]
        for optimum_position in all_optima:
            screen_pos = self.viewport.domain_to_screen(optimum_position)
            self._draw_optimum_marker(surface, screen_pos)

    @staticmethod
    def _draw_optimum_marker(surface: pygame.Surface, screen_pos: tuple[int, int]) -> None:
        color = config.COLOR_GLOBAL_OPTIMUM_MARKER
        size = 12
        x, y = screen_pos
        # Una X gruesa dentro de un círculo — distinguible a simple vista
        # de los marcadores de candidatos (círculos lisos) y del jugador.
        pygame.draw.circle(surface, color, screen_pos, size + 4, width=2)
        pygame.draw.line(surface, color, (x - size, y - size), (x + size, y + size), width=3)
        pygame.draw.line(surface, color, (x - size, y + size), (x + size, y - size), width=3)

    def _draw_overview_indicator(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont("arial", 15, bold=True)
        text = font.render("[K] MODO OBSERVADOR — vista completa", True, (255, 230, 120))
        rect = text.get_rect()
        rect.centerx = config.SCREEN_WIDTH // 2
        rect.bottom = self.playable_rect.top - 8
        surface.blit(text, rect)
# IRONEDIT:1783512345:7ea10e5589ad3a114fcc1f408fe9926ae9719f2b48f2cf5b2b42a9d4cbd532aa
