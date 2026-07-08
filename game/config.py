"""
Configuración global del juego.

Centralizar estas constantes aquí evita "números mágicos" repartidos por
todo el código, y hace trivial ajustar tamaño de pantalla, velocidades o
colores placeholder sin tener que rastrear cada archivo.
"""

# --- Ventana ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
WINDOW_TITLE = "Roguelike de Optimización — Lobby (prototipo)"

# --- Jugador ---
PLAYER_SPEED = 220.0  # píxeles por segundo
PLAYER_SIZE = (28, 36)  # ancho, alto del sprite completo (placeholder)
PLAYER_HITBOX_SIZE = (22, 14)  # hitbox de colisión: solo "los pies"

# --- Colores placeholder (sin arte todavía) ---
COLOR_BG_PLAZA = (58, 92, 62)      # verde césped apagado
COLOR_BG_SHOP = (70, 60, 50)       # marrón interior de tienda
COLOR_WALL = (40, 40, 40)
COLOR_SHOP_BUILDING = (120, 80, 60)
COLOR_DOOR = (230, 200, 90)
COLOR_PLAYER = (80, 150, 230)
COLOR_PLAYER_FACING = (20, 20, 20)
COLOR_PORTAL_UNLOCKED = (120, 210, 255)
COLOR_PORTAL_LOCKED = (110, 110, 120)
COLOR_LOCK_ICON = (20, 20, 20)
COLOR_HUD_TEXT = (255, 255, 255)
COLOR_HUD_BG = (0, 0, 0)
COLOR_MESSAGE_BG = (15, 15, 15)
COLOR_MESSAGE_TEXT = (255, 255, 255)
COLOR_PROMPT_TEXT = (255, 230, 120)

# --- Transición entre rooms ---
TRANSITION_FADE_OUT = 0.25  # segundos
TRANSITION_FADE_IN = 0.25

# --- Interacción ---
INTERACT_KEY_NAME = "E"  # solo para mostrar en prompts; el binding real va en main.py

# --- Exploración (LevelRoom / ExplorationState) ---
# Área jugable dentro de la sala de exploración, en coordenadas de PANTALLA
# (fija) — el "cuadro" tipo dig-a-hole. Centrada en la ventana, con margen
# alrededor para el HUD.
PLAYABLE_RECT_SIZE = 560
PLAYABLE_RECT_TOPLEFT = (
    (SCREEN_WIDTH - PLAYABLE_RECT_SIZE) // 2,
    (SCREEN_HEIGHT - PLAYABLE_RECT_SIZE) // 2 + 20,
)

# G: número de celdas por lado de la grid visual, usada SOLO para la
# tolerancia de "¿el jugador está parado sobre este candidato?" (no
# participa en el cálculo de zoom — ver DecisionViewport.compute_target_span).
DECISION_GRID_SIZE = 50

# Margen configurable del cálculo de zoom: cuánto más grande que el
# diámetro real de los candidatos (2x el radio máximo desde su centroide)
# debe ser el span mostrado. >1.0 siempre. Ajustable durante pruebas.
DECISION_ZOOM_MARGIN = 1.4

# Límite de seguridad de iteraciones por corrida — ajustable, igual que G.
MAX_ITERATIONS_SAFETY = 200

# Velocidad del jugador dentro de una corrida, como FRACCIÓN del span
# visible actual cruzada por segundo — así el movimiento se siente
# uniforme sin importar el nivel de zoom (a diferencia de una velocidad
# fija en unidades de dominio/seg, que se sentía vertiginosa con zoom
# amplio y casi imperceptible con zoom cerrado). Ajustable.
EXPLORATION_SPEED_SPAN_FRACTION = 0.6

# Margen extra (fracción) para el modo observador global (tecla K), para
# que el borde de bounds/trayectoria no quede pegado al borde de pantalla.
OVERVIEW_MARGIN_FACTOR = 1.15
COLOR_PLAYABLE_BG = (54, 46, 38)
COLOR_PLAYABLE_BORDER = (20, 20, 20)
COLOR_CANDIDATE_BRILLIANT = (255, 215, 90)
COLOR_CANDIDATE_GOOD = (150, 210, 150)
COLOR_CANDIDATE_NEUTRAL = (140, 140, 150)
COLOR_CANDIDATE_REJECTED = (190, 90, 90)
COLOR_TRAJECTORY_LINE = (200, 200, 210)
COLOR_GLOBAL_OPTIMUM_MARKER = (255, 60, 200)
# IRONEDIT:1783512345:08d135933b6ee73cb9da66c3dd31e6de4e491f039144198cd28001cb051a242c
