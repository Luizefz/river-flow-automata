import pygame
import numpy as np
import random
import time

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 700
CELL_SIZE = 12
FPS = 60
TITULO_JANELA = "Simulador de Fogo Florestal 3D"

GRID_COLS = 50
GRID_ROWS = 50

TREE = 1
BURNING = -1
BURNED = 2
EMPTY = 0

CELL_STATUS_LAYER = 0
CELL_ELEVATION_LAYER = 1
CELL_MOISTURE_LAYER = 2

MAX_ELEVATION = 100.0
MIN_ELEVATION = 0.0
MAX_MOISTURE = 1.0
MIN_MOISTURE = 0.0
UPHILL_MULTIPLIER = 1.6
DOWNHILL_MULTIPLIER = 1.0
TREE_DENSITY = 0.80
IGNITION_PROB = 0.7

COLOR_GROUND = (160, 82, 45)
COLOR_TREE = (0, 128, 0)
COLOR_BURNING = (255, 69, 0)
COLOR_BURNED = (40, 40, 40)
COLOR_UI_TEXT = (255, 255, 255)
COLOR_WET_TREE = (20, 90, 40)

BRUSH_FIRE = 0
BRUSH_ELEVATION = 1
BRUSH_MOISTURE = 2
ELEVATION_STEP = 2.5
MOISTURE_STEP = 0.02

MIN_BRUSH_RADIUS = 0
MAX_BRUSH_RADIUS = 10


def project_iso(x, y, z=0):
    """Converte coordenadas da grade (x, y, z) para coordenadas de tela isométricas."""
    iso_x = (x - y) * (CELL_SIZE * 0.866)  # 0.866 é cos(30)
    iso_y = (x + y) * (CELL_SIZE * 0.5) - z
    return iso_x, iso_y


origin_x = SCREEN_WIDTH // 2
origin_y = SCREEN_HEIGHT // 4


def initialize_grid(cols, rows, tree_density=TREE_DENSITY, seed=None):
    """Cria a grade 3D com base em uma seed para reprodutibilidade."""
    if seed is not None:
        random.seed(seed)

    grid = np.zeros((rows, cols, 3), dtype=float)
    for y in range(rows):
        for x in range(cols):
            if random.random() < tree_density:
                grid[y, x, CELL_STATUS_LAYER] = TREE
            else:
                grid[y, x, CELL_STATUS_LAYER] = EMPTY
            grid[y, x, CELL_ELEVATION_LAYER] = random.uniform(0, MAX_ELEVATION / 4)
            grid[y, x, CELL_MOISTURE_LAYER] = random.uniform(0.1, 0.4)
    return grid


def draw_grid(surface, grid):
    """Desenha a grade em uma projeção 3D isométrica."""
    surface.fill(COLOR_GROUND)

    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            cell_state = grid[y, x, CELL_STATUS_LAYER]
            cell_elevation = grid[y, x, CELL_ELEVATION_LAYER]
            cell_moisture = grid[y, x, CELL_MOISTURE_LAYER]

            p1 = project_iso(x, y, cell_elevation)
            p2 = project_iso(x + 1, y, cell_elevation)
            p3 = project_iso(x + 1, y + 1, cell_elevation)
            p4 = project_iso(x, y + 1, cell_elevation)

            top_color = COLOR_GROUND

            if cell_state == TREE:
                moisture_factor = cell_moisture / MAX_MOISTURE
                r = int(
                    COLOR_TREE[0] * (1 - moisture_factor)
                    + COLOR_WET_TREE[0] * moisture_factor
                )
                g = int(
                    COLOR_TREE[1] * (1 - moisture_factor)
                    + COLOR_WET_TREE[1] * moisture_factor
                )
                b = int(
                    COLOR_TREE[2] * (1 - moisture_factor)
                    + COLOR_WET_TREE[2] * moisture_factor
                )
                top_color = (r, g, b)

            elif cell_state == BURNING:
                top_color = COLOR_BURNING

            elif cell_state == BURNED:
                top_color = COLOR_BURNED

            pygame.draw.polygon(
                surface,
                top_color,
                [
                    (origin_x + p1[0], origin_y + p1[1]),
                    (origin_x + p2[0], origin_y + p2[1]),
                    (origin_x + p3[0], origin_y + p3[1]),
                    (origin_x + p4[0], origin_y + p4[1]),
                ],
            )

            side_color = (top_color[0] * 0.6, top_color[1] * 0.6, top_color[2] * 0.6)

            p_bottom_right = project_iso(x + 1, y, 0)
            pygame.draw.polygon(
                surface,
                side_color,
                [
                    (origin_x + p2[0], origin_y + p2[1]),
                    (origin_x + p_bottom_right[0], origin_y + p_bottom_right[1]),
                    (
                        origin_x + project_iso(x + 1, y + 1, 0)[0],
                        origin_y + project_iso(x + 1, y + 1, 0)[1],
                    ),
                    (origin_x + p3[0], origin_y + p3[1]),
                ],
            )

            p_bottom_left = project_iso(x, y + 1, 0)
            pygame.draw.polygon(
                surface,
                side_color,
                [
                    (origin_x + p4[0], origin_y + p4[1]),
                    (origin_x + p_bottom_left[0], origin_y + p_bottom_left[1]),
                    (
                        origin_x + project_iso(x + 1, y + 1, 0)[0],
                        origin_y + project_iso(x + 1, y + 1, 0)[1],
                    ),
                    (origin_x + p3[0], origin_y + p3[1]),
                ],
            )


def screen_to_grid(pixel_x, pixel_y):
    """Converte coordenadas de tela para coordenadas da grade na projeção isométrica."""
    px_transformed = float(pixel_x - origin_x)
    py_transformed = float(pixel_y - origin_y)
    grid_x_float = (px_transformed / (CELL_SIZE * 0.866 * 2)) + (
        py_transformed / (CELL_SIZE * 0.5 * 2)
    )
    grid_y_float = (py_transformed / (CELL_SIZE * 0.5 * 2)) - (
        px_transformed / (CELL_SIZE * 0.866 * 2)
    )
    return int(round(grid_x_float)), int(round(grid_y_float))


def start_fire(grid, grid_x, grid_y):
    if 0 <= grid_y < grid.shape[0] and 0 <= grid_x < grid.shape[1]:
        if grid[grid_y, grid_x, CELL_STATUS_LAYER] == TREE:
            grid[grid_y, grid_x, CELL_STATUS_LAYER] = BURNING
            return True
    return False


def run_step(grid):
    next_grid = grid.copy()
    rows, cols = grid.shape[:2]
    for i in range(rows):
        for j in range(cols):
            if grid[i, j, CELL_STATUS_LAYER] == BURNING:
                next_grid[i, j, CELL_STATUS_LAYER] = BURNED
            elif grid[i, j, CELL_STATUS_LAYER] == TREE:
                neighbors = [
                    (ny, nx)
                    for ny, nx in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]
                    if 0 <= ny < rows and 0 <= nx < cols
                ]
                for ny, nx in neighbors:
                    if grid[ny, nx, CELL_STATUS_LAYER] == BURNING:
                        moisture = grid[i, j, CELL_MOISTURE_LAYER]
                        prob = IGNITION_PROB * (1 - moisture)
                        elevation_tree = grid[i, j, CELL_ELEVATION_LAYER]
                        elevation_fire = grid[ny, nx, CELL_ELEVATION_LAYER]
                        if elevation_tree > elevation_fire:
                            prob *= UPHILL_MULTIPLIER
                        elif elevation_tree < elevation_fire:
                            prob *= DOWNHILL_MULTIPLIER
                        if random.random() < prob:
                            next_grid[i, j, CELL_STATUS_LAYER] = BURNING
                            break
    return next_grid


def draw_ui(surface, font, brush_mode, current_seed, brush_radius):
    y_offset = 10
    if brush_mode == BRUSH_FIRE:
        text_brush = f"Pincel: Fogo (F1) | Raio: {brush_radius}"
    elif brush_mode == BRUSH_ELEVATION:
        text_brush = f"Pincel: Elevação (F2) | Raio: {brush_radius}"
    else:
        text_brush = f"Pincel: Umidade (F3) | Raio: {brush_radius}"

    text_controls = "Controles: [ESPAÇO] Play/Pause | [R] Reset | [N] Nova Seed | [S] Salvar | [L] Carregar"
    text_seed = f"Seed Atual: {current_seed}"

    text_surface_brush = font.render(text_brush, True, COLOR_UI_TEXT)
    surface.blit(text_surface_brush, (10, y_offset))
    y_offset += 20
    text_surface_controls = font.render(text_controls, True, COLOR_UI_TEXT)
    surface.blit(text_surface_controls, (10, y_offset))
    y_offset += 20
    text_surface_seed = font.render(text_seed, True, COLOR_UI_TEXT)
    surface.blit(text_surface_seed, (10, y_offset))


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITULO_JANELA)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

current_seed = int(time.time())
terrain_grid = initialize_grid(GRID_COLS, GRID_ROWS, seed=current_seed)
fire_start_points = []

running = True
simulation_running = False
current_brush = BRUSH_FIRE
current_brush_radius = MIN_BRUSH_RADIUS

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEWHEEL:
            if event.y < 0:
                current_brush_radius = max(current_brush_radius - 1, MIN_BRUSH_RADIUS)
            elif event.y > 0:
                current_brush_radius = min(current_brush_radius + 1, MAX_BRUSH_RADIUS)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                simulation_running = not simulation_running
            if event.key == pygame.K_r:
                terrain_grid = initialize_grid(GRID_COLS, GRID_ROWS, seed=current_seed)
                fire_start_points.clear()
            if event.key == pygame.K_n:
                current_seed = int(time.time())
                terrain_grid = initialize_grid(GRID_COLS, GRID_ROWS, seed=current_seed)
                fire_start_points.clear()
            if event.key == pygame.K_s:
                with open("fire_scenario.txt", "w") as f:
                    for point in fire_start_points:
                        f.write(f"{point[0]},{point[1]}\n")
                print(f"Cenário de fogo salvo com {len(fire_start_points)} pontos.")
            if event.key == pygame.K_l:
                try:
                    with open("fire_scenario.txt", "r") as f:
                        fire_start_points.clear()
                        for line in f:
                            x_str, y_str = line.strip().split(",")
                            x, y = int(x_str), int(y_str)
                            fire_start_points.append((x, y))
                            start_fire(terrain_grid, x, y)
                    print(
                        f"Cenário de fogo carregado com {len(fire_start_points)} pontos."
                    )
                except FileNotFoundError:
                    print("Arquivo 'fire_scenario.txt' não encontrado.")
            if event.key == pygame.K_F1:
                current_brush = BRUSH_FIRE
            if event.key == pygame.K_F2:
                current_brush = BRUSH_ELEVATION
            if event.key == pygame.K_F3:
                current_brush = BRUSH_MOISTURE

    mouse_pressed = pygame.mouse.get_pressed()
    if any(mouse_pressed):
        pixel_x, pixel_y = pygame.mouse.get_pos()
        grid_x, grid_y = screen_to_grid(pixel_x, pixel_y)

        # Itera sobre a área do pincel para aplicar o efeito
        for offset_y in range(-current_brush_radius, current_brush_radius + 1):
            for offset_x in range(-current_brush_radius, current_brush_radius + 1):
                target_x = grid_x + offset_x
                target_y = grid_y + offset_y

                if 0 <= target_y < GRID_ROWS and 0 <= target_x < GRID_COLS:
                    if current_brush == BRUSH_FIRE and mouse_pressed[0]:
                        if start_fire(terrain_grid, target_x, target_y):
                            if (target_x, target_y) not in fire_start_points:
                                fire_start_points.append((target_x, target_y))
                    elif current_brush == BRUSH_ELEVATION:
                        current_elevation = terrain_grid[
                            target_y, target_x, CELL_ELEVATION_LAYER
                        ]
                        if mouse_pressed[0]:
                            new_elevation = min(
                                current_elevation + ELEVATION_STEP, MAX_ELEVATION
                            )
                            terrain_grid[target_y, target_x, CELL_ELEVATION_LAYER] = (
                                new_elevation
                            )
                        elif mouse_pressed[2]:
                            new_elevation = max(
                                current_elevation - ELEVATION_STEP, MIN_ELEVATION
                            )
                            terrain_grid[target_y, target_x, CELL_ELEVATION_LAYER] = (
                                new_elevation
                            )
                    elif current_brush == BRUSH_MOISTURE:
                        current_moisture = terrain_grid[
                            target_y, target_x, CELL_MOISTURE_LAYER
                        ]
                        if mouse_pressed[0]:
                            new_moisture = min(
                                current_moisture + MOISTURE_STEP, MAX_MOISTURE
                            )
                            terrain_grid[target_y, target_x, CELL_MOISTURE_LAYER] = (
                                new_moisture
                            )
                        elif mouse_pressed[2]:
                            new_moisture = max(
                                current_moisture - MOISTURE_STEP, MIN_MOISTURE
                            )
                            terrain_grid[target_y, target_x, CELL_MOISTURE_LAYER] = (
                                new_moisture
                            )

    if simulation_running:
        terrain_grid = run_step(terrain_grid)

    draw_grid(screen, terrain_grid)
    draw_ui(screen, font, current_brush, current_seed, current_brush_radius)

    pygame.display.flip()

pygame.quit()
