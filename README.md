# Roguelike de Optimización — Proyecto Final Optimización Multivariable

Videojuego educativo donde el jugador ejecuta, en persona, uno de cuatro
algoritmos clásicos de optimización numérica (Nelder-Mead, Hooke-Jeeves,
Recocido Simulado, Newton) sobre una de cuatro funciones de prueba
(Sphere, Himmelblau, Rastrigin, Rosenbrock), tomando en cada iteración las
mismas decisiones que tomaría alguien ejecutando el algoritmo a mano.

## Cómo correrlo

```bash
pip install -r requirements.txt
python3 main.py
```

## Cómo correr los tests (núcleo matemático + viewport + colisión)

```bash
python3 -m pytest tests/ -v
```

68 tests, cero dependencia de una ventana de pygame abierta (usan
`SDL_VIDEODRIVER=dummy` cuando hace falta pygame.Rect/font).

## Controles

**Lobby:**
- WASD / flechas — moverse
- Caminar sobre un portal de función — abre el menú de selección de
  algoritmo (si la función está desbloqueada) o muestra el costo (si no)
- **E** (parado junto al vendedor, dentro de la tienda) — abre la interfaz de compra
- ↑↓ + Enter / Esc — navegar y confirmar menús (selección de algoritmo, tienda)
- Cerrar la ventana — salir del juego (ESC ya no cierra la app; solo cancela menús)

**Dentro de una corrida de exploración:**
- WASD / flechas — moverse libremente por el área jugable
- **ESPACIO** — activar el detector: fija tu punto de partida (primera vez)
  o confirma el candidato sobre el que estás parado (iteraciones siguientes)
- **V** — "creo que aquí está el óptimo": termina la corrida voluntariamente,
  disponible desde que eliges tu punto de partida
- **K** — modo observador: aleja la cámara para ver toda la región
  relevante (bounds ∪ trayectoria ∪ candidatos); cualquier acción real
  (ESPACIO o V) te devuelve automáticamente a la vista de seguimiento
- No hay forma de salir de una corrida salvo con V (por diseño — "sala sin salida")

## Arquitectura (resumen — ver el historial de diseño para el detalle completo)

```
main.py
  └─ GameSession        (Economy + Unlocks, dueño único, persiste todo el programa)
  └─ GameStateManager    (alterna LobbyState ↔ ExplorationState)
       ├─ LobbyState      (persistente — PlazaRoom + ShopRoom vía RoomManager)
       └─ ExplorationState (una instancia nueva por corrida)
            └─ OptimizationRun   (optimization/level_room.py — motor puro, sin pygame)
                 ├─ TerrainFunction  (4 funciones, gradiente/Hessiana analíticos)
                 └─ OptimizationAlgorithm (4 algoritmos, 5 candidatos por iteración)
```

### Núcleo matemático (`optimization/`) — 100% Python puro, sin pygame

- `terrain_functions/`: Sphere, Himmelblau, Rastrigin, Rosenbrock. Cada una
  con `evaluate()`, `gradient()`, `hessian()` derivados ANALÍTICAMENTE
  (nunca por diferencias finitas, nunca suavizadas) — verificado en
  `tests/test_terrain_functions.py` contra diferencias finitas numéricas.
- `algorithms/`: cada uno mantiene su propio estado interno y expone
  `initialize/get_candidates/confirm_candidate/has_converged`. Newton
  estabiliza su Hessiana vía descomposición en eigenvalores (nunca truena
  ante Hessianas casi singulares) y expone `get_local_quadratic_model()`
  para la elipse visual. Recocido Simulado ejecuta la aceptación
  probabilística REAL en `confirm_candidate()` — el jugador puede elegir
  el mejor candidato y aun así el algoritmo lo rechace.
- `level_room.py` → `OptimizationRun`: la máquina de estados pura de una
  corrida (`CHOOSING_START → SHOWING_CANDIDATES → FINISHED`), testeable
  simulando decisiones de jugador sin ninguna ventana abierta.
- `scoring/run_result.py`: `RunResult` (snapshot fiel de una corrida) +
  `RewardStrategy` (pieza intercambiable — la fórmula actual es un
  placeholder deliberado, pendiente de balanceo tras playtesting real).

### Motor de viewport (`game/world/viewport.py`, `camera_follow.py`)

- `IdentityViewport`: 1:1, usado por el lobby.
- `DecisionViewport`: separa ESTRICTAMENTE dos responsabilidades que nunca
  se mezclan — `compute_target_span(candidate_positions, fallback_bounds)`
  calcula el zoom exclusivamente a partir de la dispersión real de los
  candidatos (centroide → radio máximo → diámetro → margen configurable
  en `config.DECISION_ZOOM_MARGIN`), con una firma que ni siquiera acepta
  la posición del jugador como parámetro — garantía estructural, no solo
  de comportamiento, de que acercarse a un candidato nunca dispara zoom.
  El CENTRO del encuadre, en cambio, es siempre `player.position`
  directamente, sin pasar por ningún cálculo de zoom.
- `CameraFollow`: suavizado exponencial continuo (independiente del
  framerate) hacia un objetivo recalculado cada frame — permite además
  el modo observador global (tecla **K**), que aleja la cámara para
  mostrar toda la región relevante sin asumir que el óptimo está en `(0,0)`.

### Progresión

- `Economy`/`Unlocks` viven en `GameSession`, compartidos entre lobby y
  exploración — las monedas ganadas en una corrida se reflejan de
  inmediato al volver al lobby.
- Catálogo: 1 función (Sphere) y 1 algoritmo (Recocido Simulado)
  desbloqueados por defecto; los otros 6 ítems cuestan 10 monedas cada
  uno (`game/data/*_config.py`).
- Recompensa placeholder: `100 × progreso_relativo × multiplicador`, con
  `SCORING_MULTIPLIERS` (tabla 4×4) en 1.0 para las 16 combinaciones —
  pendiente de balanceo real tras las primeras partidas de prueba.

## Qué es intencionalmente un placeholder / trabajo futuro

- Todo el arte son formas geométricas de color — sin sprites ni animaciones.
- La fórmula de recompensa sigue siendo un placeholder — el costo de la
  tienda está temporalmente en 100 monedas uniformes por ítem (pedido
  explícito del equipo), pendiente de ajuste junto con el sistema de
  economía completo.
- No hay persistencia entre ejecuciones (`GameSession` se crea nueva cada
  vez que corres `main.py`).

## Historial de correcciones tras el primer playtesting real

- **Eje Y invertido en exploración**: corregido con `Viewport.y_axis_sign()`.
- **Crash al declarar victoria en "ronda cero"**: guardia explícita en
  `OptimizationRun.declare_victory()` + mensaje amable en `ExplorationState`.
- **Zoom agresivo al acercarse a un candidato**: `DecisionViewport.compute_target_span()`
  ahora tiene una firma que ni siquiera acepta la posición del jugador —
  el cálculo depende exclusivamente de la dispersión real de los
  candidatos (centroide → radio máximo → diámetro → margen configurable).
- **Cámara inconsistente**: reemplazado el criterio de "distancia mínima
  entre pares" (muy sensible a un solo par atípico) por uno robusto
  basado en la dispersión total del conjunto.
- **Movimiento imperceptible antes de elegir el punto de partida**: la
  cámara ahora se queda FIJA en el centro del dominio durante
  `CHOOSING_START` (en vez de perseguir al jugador tan de cerca que
  cancelaba casi todo el desplazamiento visible).
- **Velocidad inconsistente con el zoom**: la velocidad del jugador ahora
  es una fracción configurable del span visible actual (`config.EXPLORATION_SPEED_SPAN_FRACTION`).
- **ESC cerraba todo el juego**: ya no se intercepta globalmente en
  `main.py` — cada estado decide localmente qué hacer con esa tecla.
- **Marcador del óptimo global**: visible al finalizar la corrida, con la
  cámara abriéndose automáticamente para mostrar tanto el resultado real
  como el óptimo esperado a la vez (incluye los 4 óptimos de Himmelblau).
- **Tienda funcional**: `ShopVendorInteractable` (tecla E) abre una
  interfaz de compra real, conectada a `Economy`/`Unlocks`.

## Estructura completa de archivos

Ver `find . -name "*.py"` — 64 archivos organizados en `game/` (motor de
juego, pygame) y `optimization/` (núcleo matemático, puro Python),
más `tests/` (68 tests con pytest).
