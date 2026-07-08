"""
Método de Newton.

Estado interno: posición actual (x,y).

Dirección de búsqueda: d = -H^-1 * grad(f), pero la Hessiana real puede ser
casi singular (uno de sus eigenvalores cerca de 0) o indefinida (eigenvalores
de signos distintos, típico cerca de sillas de montar) — en ambos casos,
invertirla directamente puede producir una dirección inútil o inestable.

Estabilización aplicada (variante de Newton modificado / Levenberg-Marquardt):
  1. Se descompone H en eigenvalores/eigenvectores: H = V diag(lambda) V^T
     (válido porque H siempre es simétrica en este contexto).
  2. Se reemplaza cada eigenvalor por max(|lambda_i|, MIN_EIGENVALUE) —
     esto garantiza una matriz SIEMPRE definida positiva y bien
     condicionada, sin importar qué tan patológica sea la H real en ese
     punto.
  3. La dirección se calcula con esa Hessiana estabilizada.

Esta misma descomposición se expone vía get_local_quadratic_model(), usada
por el renderer para dibujar la elipse de la aproximación cuadrática local
(eje mayor/menor = eigenvectores, escala de cada semieje = 1/sqrt(eigenvalor)).

Los 5 candidatos son 5 tamaños de paso alpha a lo largo de la ÚNICA
dirección de Newton (no 5 direcciones distintas) — esto simula la búsqueda
unidireccional (line search) que exige la rúbrica.

Criterio de paro: ||grad f|| <= epsilon.
"""

from __future__ import annotations

import numpy as np

from optimization.algorithms.base import Candidate, OptimizationAlgorithm, label_candidates_by_rank
from optimization.terrain_functions.base import TerrainFunction

EPSILON_GRADIENT = 1e-3
MIN_EIGENVALUE = 1e-2  # piso de estabilización — evita división por ~0
ALPHA_STEPS = (0.25, 0.5, 1.0, 1.5, 2.0)


class Newton(OptimizationAlgorithm):
    id = "newton"
    name = "Newton"

    def initialize(self, x0: tuple[float, float], terrain: TerrainFunction) -> None:
        self.terrain = terrain
        self.position = x0
        self.value = terrain.evaluate(*x0)
        self.iterations_used = 0

    def _compute_direction_and_model(self, position: tuple[float, float]):
        """Devuelve (direccion (2,) ndarray, eigenvalues, eigenvectors) en
        ese punto, con la Hessiana ya estabilizada."""
        x, y = position
        gx, gy = self.terrain.gradient(x, y)
        grad = np.array([gx, gy])

        (hxx, hxy), (hyx, hyy) = self.terrain.hessian(x, y)
        H = np.array([[hxx, hxy], [hyx, hyy]])

        eigenvalues, eigenvectors = np.linalg.eigh(H)  # simétrica -> eigh
        stabilized = np.maximum(np.abs(eigenvalues), MIN_EIGENVALUE)

        # H_stable^-1 = V * diag(1/stabilized) * V^T
        H_inv_stable = eigenvectors @ np.diag(1.0 / stabilized) @ eigenvectors.T
        direction = -H_inv_stable @ grad

        return direction, eigenvalues, eigenvectors

    def get_candidates(self) -> list[Candidate]:
        direction, _, _ = self._compute_direction_and_model(self.position)
        x, y = self.position

        positions = []
        f_values = []
        for alpha in ALPHA_STEPS:
            px = float(x + alpha * direction[0])
            py = float(y + alpha * direction[1])
            positions.append((px, py))
            f_values.append(self.terrain.evaluate(px, py))

        labels = label_candidates_by_rank(f_values)
        operation_labels = [f"alpha={a}" for a in ALPHA_STEPS]

        return [
            Candidate(position=positions[i], f_value=f_values[i], quality_label=labels[i],
                      operation_label=operation_labels[i])
            for i in range(5)
        ]

    def confirm_candidate(self, candidate: Candidate) -> Candidate:
        self.position = candidate.position
        self.value = candidate.f_value
        self.iterations_used += 1
        return candidate

    def has_converged(self) -> bool:
        return self.terrain.gradient_norm(*self.position) <= EPSILON_GRADIENT

    def get_convergence_indicator(self) -> float:
        return self.terrain.gradient_norm(*self.position)

    def get_current_position(self) -> tuple[float, float]:
        return self.position

    def get_current_value(self) -> float:
        return self.value

    def get_local_quadratic_model(self):
        """Método adicional, específico de Newton (no forma parte del
        contrato base): eigenvalores/eigenvectores de la Hessiana REAL
        (sin estabilizar — para la elipse queremos mostrar la curvatura
        real, incluyendo cuándo se vuelve patológica) en la posición
        actual. Usado por el renderer para dibujar la elipse."""
        x, y = self.position
        (hxx, hxy), (hyx, hyy) = self.terrain.hessian(x, y)
        H = np.array([[hxx, hxy], [hyx, hyy]])
        eigenvalues, eigenvectors = np.linalg.eigh(H)
        return eigenvalues, eigenvectors
# IRONEDIT:1783483892:e776cfff6767ceb1b9e9f830ba9a4f54bb3283b58d425ac4b5670209059540ea
