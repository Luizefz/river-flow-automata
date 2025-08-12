"""Simulação de entulhos em um rio com base em um modelo de autômato celular."""

import numpy as np
import matplotlib.pyplot as plt

class River:
    def __init__(self, length, width, river_deformation="L"):
        self.length = length
        self.width = width
        self.river_deformation = river_deformation
        self.grid = np.zeros((length, width), dtype=int)
        
    def initialize_river(self):
        """Inicializa o rio com uma deformação específica."""
        if self.river_deformation == "L":
            self.grid[:, 0] = 1  # Deformação em forma de L
        elif self.river_deformation == "U":
            self.grid[0, :] = 1
            
    def show_river(self):
        """Exibe o estado atual do rio."""
        ax = plt.subplots(2,2, figsize=(16, 12))
        ax[0, 0].imshow(self.grid, cmap="Blues")
        ax[0, 0].set_title("Estado do Rio")
        ax[0, 1].hist(self.grid.ravel(), bins=10, color="blue", alpha=0.7)
        ax[0, 1].set_title("Distribuição de Entulhos")
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.show()