"""
OptimizationRun: el "cerebro" de una corrida completa. NO sabe nada de
pygame, viewport, ni HUD — game/states/exploration_state.py lo envuelve y
lo dibuja. Esto permite testear el flujo completo de una partida
(elegir x0 -> ver candidatos -> confirmar -> ... -> declarar victoria)
con pytest puro, simulando exactamente las decisiones de un jugador.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from optimization.algorithms.base import Candidate, OptimizationAlgorithm
from optimization.scoring.run_result import RunResult
from optimization.terrain_functions.base import TerrainFunction

DEFAULT_MAX_ITERATIONS = 200


class RunPhase(Enum):
    CHOOSING_START = auto()
    SHOWING_CANDIDATES = auto()
    FINISHED = auto()


class OptimizationRun:
    def __init__(
        self,
        terrain: TerrainFunction,
        algorithm: OptimizationAlgorithm,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        self.terrain = terrain
        self.algorithm = algorithm
        self.max_iterations = max_iterations

        self.phase = RunPhase.CHOOSING_START
        self.trajectory: list[tuple[tuple[float, float], float]] = []
        self.current_candidates: list[Candidate] = []
        self.last_confirmed_candidate: Optional[Candidate] = None

        self._x_start: Optional[tuple[float, float]] = None
        self._f_start: Optional[float] = None
        self.result: Optional[RunResult] = None

    # ------------------------------------------------------------------
    def choose_start(self, x0: tuple[float, float]) -> None:
        if self.phase != RunPhase.CHOOSING_START:
            raise RuntimeError("choose_start() solo es válido en la fase CHOOSING_START")

        self.algorithm.initialize(x0, self.terrain)
        self._x_start = x0
        self._f_start = self.terrain.evaluate(*x0)
        self.trajectory.append((x0, self._f_start))

        self.current_candidates = self.algorithm.get_candidates()
        self.phase = RunPhase.SHOWING_CANDIDATES

    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        """Ejecuta la iteración real. Devuelve el candidato EFECTIVAMENTE
        aceptado (puede diferir del elegido para Recocido Simulado)."""
        if self.phase != RunPhase.SHOWING_CANDIDATES:
            raise RuntimeError("confirm_candidate() solo es válido en SHOWING_CANDIDATES")

        accepted = self.algorithm.confirm_candidate(candidate)
        self.last_confirmed_candidate = accepted
        self.trajectory.append((accepted.position, accepted.f_value))

        if self.algorithm.iterations_used >= self.max_iterations:
            self._finish(ended_by_player=False)
            return accepted

        self.current_candidates = self.algorithm.get_candidates()
        return accepted

    def declare_victory(self) -> RunResult:
        """El jugador presiona 'creo que aquí está el óptimo', disponible
        desde que se elige x0 (0 iteraciones adicionales requeridas) —
        pero NO antes de elegir x0 siquiera, ya que en ese punto no existe
        ninguna posición ni valor de f que reportar como resultado."""
        if self.phase == RunPhase.CHOOSING_START:
            raise RuntimeError(
                "No se puede declarar victoria antes de elegir un punto de "
                "partida — llama a choose_start() primero."
            )
        if self.phase == RunPhase.FINISHED:
            raise RuntimeError("La corrida ya había terminado")
        self._finish(ended_by_player=True)
        assert self.result is not None
        return self.result

    def _finish(self, ended_by_player: bool) -> None:
        current_position, current_value = self.trajectory[-1]
        self.result = RunResult(
            terrain_function_id=self.terrain.id,
            algorithm_id=self.algorithm.id,
            iterations_used=self.algorithm.iterations_used,
            x_start=self._x_start,
            x_final=current_position,
            f_start=self._f_start,
            f_final=current_value,
            global_optimum_value=self.terrain.global_optimum_value,
            ended_by_player=ended_by_player,
        )
        self.phase = RunPhase.FINISHED

    def is_finished(self) -> bool:
        return self.phase == RunPhase.FINISHED

    def get_convergence_indicator(self) -> Optional[float]:
        if self.phase == RunPhase.CHOOSING_START:
            return None
        return self.algorithm.get_convergence_indicator()
# IRONEDIT:1783483892:fdd82771da4d69699f6acfdca214295710fcf792ee3bb94dc69a48050bf609f0
