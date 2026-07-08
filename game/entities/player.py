"""
Entidad del jugador.

Deliberadamente no conoce nada sobre "rooms": recibe input crudo y una
lista de rectángulos de colisión, y resuelve su propio movimiento. Esto
mantiene el acoplamiento en una sola dirección (Room conoce al Player
momentáneamente durante update(), Player no conoce a ninguna Room).

IMPORTANTE (retrofit para soportar LevelRoom/ExplorationState): self.position
puede vivir en dos "espacios" distintos según el contexto:
  - En el lobby (PlazaRoom/ShopRoom): coordenadas de PANTALLA (píxeles),
    con IdentityViewport haciendo de traducción trivial.
  - En una corrida de exploración: coordenadas de DOMINIO (los mismos
    números que usa la matemática real, sin ninguna transformación).

Por eso get_hitbox()/try_move()/draw() reciben SIEMPRE un Viewport
explícito: el hitbox y la colisión se resuelven en espacio de PANTALLA
(donde el tamaño en píxeles del jugador tiene sentido), sin importar en
qué espacio viva self.position.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Iterable

import pygame

from game import config
from game.world.viewport import Viewport


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


class Player:
    def __init__(self, start_pos: tuple[float, float]) -> None:
        # position es el CENTRO del sprite completo. Su "espacio" (píxeles
        # de pantalla o unidades de dominio) depende del contexto — ver
        # docstring del módulo.
        self.position = pygame.Vector2(start_pos)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = config.PLAYER_SPEED  # unidades de self.position por segundo

        self.sprite_size = config.PLAYER_SIZE  # SIEMPRE en píxeles (tamaño en pantalla)
        self.hitbox_size = config.PLAYER_HITBOX_SIZE  # SIEMPRE en píxeles

        self.facing = Direction.DOWN

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        move = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move.y += 1

        # Normalizar para que moverse en diagonal no sea más rápido
        # (sin esto, mover X e Y a la vez suma velocidad en ambos ejes
        # y el jugador avanza sqrt(2) veces más rápido en diagonal).
        if move.length_squared() > 0:
            move = move.normalize()
            self._update_facing(move)

        self.velocity = move * self.speed

    def _update_facing(self, move: pygame.Vector2) -> None:
        # Prioriza el eje dominante para decidir hacia dónde "mira" el jugador.
        if abs(move.x) > abs(move.y):
            self.facing = Direction.RIGHT if move.x > 0 else Direction.LEFT
        else:
            self.facing = Direction.DOWN if move.y > 0 else Direction.UP

    # ------------------------------------------------------------------
    # Movimiento y colisión — SIEMPRE en espacio de PANTALLA vía viewport
    # ------------------------------------------------------------------
    def get_hitbox(self, viewport: Viewport) -> pygame.Rect:
        screen_x, screen_y = viewport.domain_to_screen((self.position.x, self.position.y))
        hw, hh = self.hitbox_size
        # El hitbox se ancla a la mitad inferior del sprite (simula "los pies"),
        # no al centro completo del sprite. El sprite siempre se dibuja del
        # mismo tamaño en píxeles, sin importar el zoom del viewport —
        # solo su POSICIÓN cambia con el zoom, no su tamaño en pantalla.
        cx = screen_x
        cy = screen_y + (self.sprite_size[1] / 2) - (hh / 2)
        return pygame.Rect(0, 0, hw, hh).move(cx - hw / 2, cy - hh / 2)

    def try_move(
        self, dt: float, collision_rects: Iterable[pygame.Rect], viewport: Viewport
    ) -> None:
        """Idéntica precisión que la versión original (corrección exacta
        de sub-píxel, resuelta eje por eje para evitar el bug clásico de
        quedar 'atorado' en esquinas al moverse en diagonal), pero ahora
        la corrección se calcula en espacio de PANTALLA y se convierte de
        vuelta a las unidades de self.position vía viewport.screen_to_domain()
        — así funciona exacto tanto si self.position vive en píxeles
        (IdentityViewport, lobby) como en coordenadas de dominio
        (DecisionViewport, exploración), sin asumir ninguna relación de
        escala fija entre ambos espacios."""
        collision_rects = list(collision_rects)

        # --- Eje X ---
        self.position.x += self.velocity.x * dt
        hitbox = self.get_hitbox(viewport)
        for rect in collision_rects:
            if hitbox.colliderect(rect):
                overlap_px = 0.0
                if self.velocity.x > 0:
                    overlap_px = hitbox.right - rect.left
                elif self.velocity.x < 0:
                    overlap_px = -(rect.right - hitbox.left)
                if overlap_px != 0.0:
                    self._shift_position_by_screen_delta(viewport, dx_px=-overlap_px, dy_px=0.0)
                hitbox = self.get_hitbox(viewport)

        # --- Eje Y ---
        # velocity.y > 0 SIEMPRE significa "intención de bajar en pantalla"
        # (así lo define Player.handle_input, de forma agnóstica al
        # espacio en que viva self.position). Pero el DELTA real que hay
        # que sumarle a self.position.y para lograr ese efecto visual
        # depende del viewport (ver Viewport.y_axis_sign) — por eso el
        # signo se aplica aquí, en la integración, y NO en handle_input.
        y_sign = viewport.y_axis_sign()
        self.position.y += self.velocity.y * dt * y_sign
        hitbox = self.get_hitbox(viewport)
        for rect in collision_rects:
            if hitbox.colliderect(rect):
                overlap_px = 0.0
                if self.velocity.y > 0:
                    overlap_px = hitbox.bottom - rect.top
                elif self.velocity.y < 0:
                    overlap_px = -(rect.bottom - hitbox.top)
                if overlap_px != 0.0:
                    self._shift_position_by_screen_delta(viewport, dx_px=0.0, dy_px=-overlap_px)
                hitbox = self.get_hitbox(viewport)

    def _shift_position_by_screen_delta(
        self, viewport: Viewport, dx_px: float, dy_px: float
    ) -> None:
        """Desplaza self.position lo necesario para que su proyección en
        pantalla se mueva exactamente (dx_px, dy_px) píxeles — sin asumir
        ninguna escala fija, usando el propio viewport como fuente de verdad
        de la conversión (funciona igual de exacto para 1:1 o para zoom)."""
        current_screen = viewport.domain_to_screen((self.position.x, self.position.y))
        target_screen = (current_screen[0] + dx_px, current_screen[1] + dy_px)
        target_domain = viewport.screen_to_domain(target_screen)
        self.position.x = target_domain[0]
        self.position.y = target_domain[1]

    def set_position(self, pos: tuple[float, float]) -> None:
        """Teletransporta al jugador (usado por RoomManager tras una transición,
        o por ExplorationState al fijar x0), separado deliberadamente de
        try_move() que es solo para input normal."""
        self.position = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(0, 0)

    # ------------------------------------------------------------------
    # Dibujo (placeholder: rectángulo de color + marca de dirección)
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, viewport: Viewport) -> None:
        screen_pos = viewport.domain_to_screen((self.position.x, self.position.y))
        w, h = self.sprite_size
        rect = pygame.Rect(0, 0, w, h)
        rect.center = screen_pos
        pygame.draw.rect(surface, config.COLOR_PLAYER, rect, border_radius=4)

        # Pequeña marca que indica hacia dónde mira, útil como placeholder
        # antes de tener animaciones direccionales reales.
        cx, cy = rect.center
        mark_len = 10
        offsets = {
            Direction.UP: (0, -mark_len),
            Direction.DOWN: (0, mark_len),
            Direction.LEFT: (-mark_len, 0),
            Direction.RIGHT: (mark_len, 0),
        }
        dx, dy = offsets[self.facing]
        pygame.draw.line(
            surface, config.COLOR_PLAYER_FACING, (cx, cy), (cx + dx, cy + dy), 3
        )

        # Debug opcional: descomentar para ver el hitbox real
        # pygame.draw.rect(surface, (255, 0, 0), self.get_hitbox(viewport), 1)
# IRONEDIT:1783483891:42ba9fc86a4525ef085df215f8dfe5183c4a4b77975ed053983311dfd449af09
