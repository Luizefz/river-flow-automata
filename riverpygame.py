import pygame
import sys
import numpy as np
import math
from enum import IntEnum
from functools import lru_cache

# =============================================================================
# 1. CONFIGURAÇÃO E CONSTANTES GLOBAIS
# =============================================================================
GRID_WIDTH, GRID_HEIGHT, HEX_SIZE, FPS = 20, 20, 20, 15
TITULO_JANELA = "Autômato Celular de Gás de Rede (FHP Minimalista)"
SCREEN_WIDTH = int(GRID_WIDTH * HEX_SIZE * 1.5 + HEX_SIZE)
SCREEN_HEIGHT = int(GRID_HEIGHT * HEX_SIZE * math.sqrt(3) + HEX_SIZE)

# --- Cores minimalistas ---
COR_FUNDO = (25, 30, 40)  # Fundo escuro, neutro
COR_HEX_VAZIO = (50, 60, 70)  # Hex vazio em tom médio
COR_HEX_OBSTACULO = (120, 80, 120)  # Obstáculos cinza
COR_HEX_FONTE = (100, 120, 150)  # Fontes azul suave
COR_PARTICULA = (130, 170, 220, 180)  # Azul claro com transparência alfa
COR_CONTORNO_HEX = (80, 90, 100)  # Contorno sutil
COR_TEXTO = (200, 210, 220)  # Texto cinza claro


# --- Definições do Autômato ---
class Particula(IntEnum):
    E = 1 << 0  # Leste
    SE = 1 << 1  # Sudeste
    SW = 1 << 2  # Sudoeste
    W = 1 << 3  # Oeste
    NW = 1 << 4  # Noroeste
    NE = 1 << 5  # Nordeste


VETORES_DIRECAO = {
    Particula.E: (1, 0),
    Particula.SE: (0.5, -np.sqrt(3) / 2),
    Particula.SW: (-0.5, -np.sqrt(3) / 2),
    Particula.W: (-1, 0),
    Particula.NW: (-0.5, np.sqrt(3) / 2),
    Particula.NE: (0.5, np.sqrt(3) / 2),
}


# =============================================================================
# 2. CLASSE PRINCIPAL DA SIMULAÇÃO
# =============================================================================
class Simulacao:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITULO_JANELA)
        # Fonte moderna e simples
        self.font = pygame.font.SysFont("Calibri", 14)
        self.clock = pygame.time.Clock()

        self.rodando = True
        self.simulacao_iniciada = False
        self.delay_mouse = 0
        self.limpar_grade()

        self.MAPA_DIRECOES_OPOSTAS = self._criar_mapa_opostos()
        self.REGRAS_DE_COLISAO = self._criar_regras_colisao()
        self._preparar_desenho()

    def _criar_mapa_opostos(self):
        return {
            Particula.E: Particula.W,
            Particula.W: Particula.E,
            Particula.NE: Particula.SW,
            Particula.SW: Particula.NE,
            Particula.NW: Particula.SE,
            Particula.SE: Particula.NW,
        }

    def _criar_regras_colisao(self):
        regras = {}
        pares_reversiveis = [
            (52, 25),
            (50, 41),
            (38, 11),
            (22, 13),
            (37, 19),
            (26, 44),
            (21, 42),
            (27, 45),
            (45, 54),
            (54, 27),
            (36, 18),
            (18, 9),
            (9, 36),
        ]
        for a, b in pares_reversiveis:
            regras[a] = b
            regras[b] = a
        return regras

    def _preparar_desenho(self):
        self.offsets_hexagono = [
            (
                HEX_SIZE * math.cos(math.radians(60 * i + 30)),
                HEX_SIZE * math.sin(math.radians(60 * i + 30)),
            )
            for i in range(6)
        ]
        self.vetores_desenho = {p: (v[0], -v[1]) for p, v in VETORES_DIRECAO.items()}

    def limpar_grade(self):
        self.estados = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.obstaculos = [[False] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.fontes = [[False] * GRID_WIDTH for _ in range(GRID_HEIGHT)]

    def _atualizar_estado(self):
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                if self.fontes[r][c]:
                    self.estados[r][c] |= Particula.SE | Particula.SW

        estados_colididos = [
            [
                self.REGRAS_DE_COLISAO.get(self.estados[r][c], self.estados[r][c])
                for c in range(GRID_WIDTH)
            ]
            for r in range(GRID_HEIGHT)
        ]

        novos_estados = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                estado_celula = estados_colididos[r][c]
                if not estado_celula:
                    continue
                for particula in Particula:
                    if estado_celula & particula:
                        nr, nc = self._get_vizinho(r, c, particula)
                        if (
                            0 <= nr < GRID_HEIGHT
                            and 0 <= nc < GRID_WIDTH
                            and not self.obstaculos[nr][nc]
                        ):
                            novos_estados[nr][nc] |= particula
                        else:
                            novos_estados[r][c] |= self.MAPA_DIRECOES_OPOSTAS[particula]
        self.estados = novos_estados

    @staticmethod
    @lru_cache(maxsize=None)
    def _get_vizinho(r, c, direcao):
        idx = int(math.log2(direcao))
        if c % 2 == 0:
            offsets = [
                (r, c + 1),
                (r + 1, c),
                (r + 1, c - 1),
                (r, c - 1),
                (r - 1, c - 1),
                (r - 1, c),
            ]
        else:
            offsets = [
                (r, c + 1),
                (r + 1, c + 1),
                (r + 1, c),
                (r, c - 1),
                (r - 1, c),
                (r - 1, c + 1),
            ]
        return offsets[idx]

    def _desenhar(self):
        self.display.fill(COR_FUNDO)
        surface_particulas = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )

        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                cor_hex = COR_HEX_VAZIO
                if self.obstaculos[r][c]:
                    cor_hex = COR_HEX_OBSTACULO
                elif self.fontes[r][c]:
                    cor_hex = COR_HEX_FONTE

                centro = self._hex_para_pixel(r, c)
                pontos = [
                    (centro[0] + dx, centro[1] + dy) for dx, dy in self.offsets_hexagono
                ]

                pygame.draw.polygon(self.display, cor_hex, pontos)
                pygame.draw.polygon(self.display, COR_CONTORNO_HEX, pontos, 1)

                if self.estados[r][c]:
                    for particula in Particula:
                        if self.estados[r][c] & particula:
                            vetor = self.vetores_desenho[particula]
                            ponta = (
                                centro[0] + vetor[0] * HEX_SIZE * 0.7,
                                centro[1] + vetor[1] * HEX_SIZE * 0.7,
                            )
                            pygame.draw.line(
                                surface_particulas, COR_PARTICULA, centro, ponta, 1
                            )
                            pygame.draw.circle(
                                surface_particulas, COR_PARTICULA, ponta, 2
                            )

        self.display.blit(surface_particulas, (0, 0))

        status_texto = "Rodando" if self.simulacao_iniciada else "Pausado"
        texto_surface = self.font.render(
            f"Simulação: {status_texto}  (Espaço p/ start/pause)", True, COR_TEXTO
        )
        self.display.blit(texto_surface, (10, 10))

        pygame.display.update()

    def _processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (
                evento.type == pygame.KEYDOWN
                and evento.key in (pygame.K_q, pygame.K_ESCAPE)
            ):
                self.rodando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    self.simulacao_iniciada = not self.simulacao_iniciada
                if evento.key == pygame.K_c:
                    self.limpar_grade()

        if self.delay_mouse <= 0:
            botoes = pygame.mouse.get_pressed()
            if botoes[0] or botoes[2]:
                r, c = self._pixel_para_hex(pygame.mouse.get_pos())
                if r != -1:
                    if botoes[0]:
                        self.fontes[r][c] = not self.fontes[r][c]
                    if botoes[2]:
                        self.obstaculos[r][c] = not self.obstaculos[r][c]
                    self.delay_mouse = 12
        else:
            self.delay_mouse -= 1

    def _hex_para_pixel(self, r, c):
        x = HEX_SIZE * 1.5 * c + HEX_SIZE
        y = HEX_SIZE * math.sqrt(3) * (r + 0.5 * (c % 2)) + HEX_SIZE
        return int(x), int(y)

    def _pixel_para_hex(self, pos):
        px, py = pos
        hex_mais_proximo = (-1, -1)
        min_dist_sq = float("inf")
        est_c = int((px - HEX_SIZE) / (HEX_SIZE * 1.5))
        est_r = int((py - HEX_SIZE) / (HEX_SIZE * math.sqrt(3)) - 0.5 * (est_c % 2))

        for r_off in range(-2, 3):
            for c_off in range(-2, 3):
                r, c = est_r + r_off, est_c + c_off
                if 0 <= r < GRID_HEIGHT and 0 <= c < GRID_WIDTH:
                    hex_px, hex_py = self._hex_para_pixel(r, c)
                    dist_sq = (hex_px - px) ** 2 + (hex_py - py) ** 2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        hex_mais_proximo = (r, c)
        return hex_mais_proximo

    def rodar(self):
        while self.rodando:
            self._processar_eventos()
            if self.simulacao_iniciada:
                self._atualizar_estado()
            self._desenhar()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


# =============================================================================
# 3. PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    sim = Simulacao()
    sim.rodar()
