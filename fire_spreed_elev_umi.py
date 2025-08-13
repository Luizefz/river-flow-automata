import pygame
import numpy as np
import random

# --- Configurações ---
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 500
CELL_SIZE = 8
FPS = 60
TITULO_JANELA = "Simulador de Fogo Florestal com Elevação e Umidade"

GRID_COLS = SCREEN_WIDTH // CELL_SIZE
GRID_ROWS = SCREEN_HEIGHT // CELL_SIZE

# CELL possible Status
TREE = 1
BURNING = -1
BURNED = 2
EMPTY = 0

# CELL caracterisctics layer
CELL_STATUS_LAYER = 0
CELL_ELEVATION_LAYER = 1
CELL_MOISTURE_LAYER = 2

# Multiplyers for random generation
MAX_ELEVATION = 100
UPHILL_MULTIPLIER = 1.6
DOWNHILL_MULTIPLIER = 1.0
TREE_DENSITY = 0.80
IGNITION_PROB = 0.72

# CELL Status colors
COLOR_GROUND = (160, 82, 45)
COLOR_TREE = (0, 128, 0)
COLOR_BURNING = (255, 69, 0)
COLOR_BURNED = (40, 40, 40)


def initialize_grid(cols, rows, tree_density=TREE_DENSITY):
    grid = np.zeros((rows, cols, 3), dtype=float)
    for y in range(rows):
        for x in range(cols):
            if random.random() < tree_density:
                grid[y, x, CELL_STATUS_LAYER] = TREE
            else:
                grid[y, x, CELL_STATUS_LAYER] = EMPTY
            grid[y, x, CELL_ELEVATION_LAYER] = random.randint(0, MAX_ELEVATION)
            grid[y, x, CELL_MOISTURE_LAYER] = random.uniform(0.1, 0.4)
    return grid


def draw_grid(surface, grid):
    for y in range(grid.shape[0]):
        for x in range(grid.shape[1]):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            cell_state = grid[y, x, CELL_STATUS_LAYER]
            cell_elevation = grid[y, x, CELL_ELEVATION_LAYER]
            cell_moisture = grid[y, x, CELL_MOISTURE_LAYER]
            base_color = COLOR_GROUND

            if cell_state == TREE:
                base_color = COLOR_TREE

            elif cell_state == BURNING:
                base_color = COLOR_BURNING

            elif cell_state == BURNED:
                base_color = COLOR_BURNED

            brightness_factor = 0.7 + ((cell_elevation / MAX_ELEVATION * 0.6) + (cell_moisture / 0.4 * 0.4))
            final_color = (
                min(255, int(base_color[0] * brightness_factor)),
                min(255, int(base_color[1] * brightness_factor)),
                min(255, int(base_color[2] * brightness_factor)),
            )
            pygame.draw.rect(surface, final_color, rect)


def draw_start_fire(grid, grid_x, grid_y):
    if 0 <= grid_y < grid.shape[0] and 0 <= grid_x < grid.shape[1]:
        if grid[grid_y, grid_x, CELL_STATUS_LAYER] == TREE:
            grid[grid_y, grid_x, CELL_STATUS_LAYER] = BURNING


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


# --- Inicialização e Loop Principal ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITULO_JANELA)
clock = pygame.time.Clock()
terrain_grid = initialize_grid(GRID_COLS, GRID_ROWS)

running = True
simulation_running = False

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                simulation_running = not simulation_running
            if event.key == pygame.K_r:
                terrain_grid = initialize_grid(GRID_COLS, GRID_ROWS)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pixel_x, pixel_y = event.pos
            grid_x = pixel_x // CELL_SIZE
            grid_y = pixel_y // CELL_SIZE
            draw_start_fire(terrain_grid, grid_x, grid_y)

    if simulation_running:
        terrain_grid = run_step(terrain_grid)

    screen.fill(COLOR_GROUND)
    draw_grid(screen, terrain_grid)
    pygame.display.flip()

pygame.quit()
