import numpy as np
from noise import pnoise2
import time
from config import GRID_SIZE, BIOME_SIZE, BIOME_GRID_SHAPE

class TerrainModel:
    """
    Cada bioma possui seu próprio parâmetro de escala para o Perlin.
    """

    GLOBAL_SEED = 242

    def __init__(self, biomes_data=None):

        self.shape = (GRID_SIZE, GRID_SIZE)
        self.BIOME_SIZE = BIOME_SIZE
        self.BIOME_GRID_SHAPE = BIOME_GRID_SHAPE
        self.Z_offset = np.zeros(self.shape)
        # define dados dos biomas
        if biomes_data is None:
            self.biomes_params = self._initialize_default_biomes()
        else:
            self.biomes_params = biomes_data

        # malha X/Y
        self.X, self.Y = np.meshgrid(
            np.arange(self.shape[0]),
            np.arange(self.shape[1])
        )

        self.Z_base = np.zeros(self.shape)
        self.X_flat = self.X.ravel()
        self.Y_flat = self.Y.ravel()


        # geração inicial
        self.generate_full_noise()

        # -------------------------
    # Helpers públicos
    # -------------------------
    def set_biome_scale(self, r, c, value):
        self.biomes_params[r, c]["scale"] = float(value)

    def get_biome_scale(self, r, c):
        return float(self.biomes_params[r, c]["scale"])

    
    def _initialize_default_biomes(self):
        """Cada bioma recebe uma escala entre 0.01 e 0.1."""
        biomes = np.empty(self.BIOME_GRID_SHAPE, dtype=object)

        for r in range(self.BIOME_GRID_SHAPE[0]):
            for c in range(self.BIOME_GRID_SHAPE[1]):
                biomes[r, c] = {
                    "scale": 0.01 + 0.01 * np.random.rand()
                }

        return biomes

    def generate_full_noise(self):
        """Gera Perlin Noise aplicando o parâmetro de cada bioma."""
        start = time.time()
        R, C = self.shape

        for i in range(R):
            for j in range(C):
                biome_r = i // self.BIOME_SIZE
                biome_c = j // self.BIOME_SIZE
                scale = self.biomes_params[biome_r, biome_c]["scale"]

                self.Z_base[i, j] = pnoise2(
                    i * scale,
                    j * scale,
                    octaves=6,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=R,
                    repeaty=C,
                    base=self.GLOBAL_SEED
                )

        # normalização
        mn, mx = self.Z_base.min(), self.Z_base.max()
        self.Z_base = (self.Z_base - mn) / (mx - mn)

        print(f"[TerrainModel] Geração completa ({GRID_SIZE}x{GRID_SIZE}) em {time.time() - start:.2f}s")

    def get_points_data(self, amplitude):
        Z = self.Z_base.ravel() * (amplitude / 10.0)
        return np.column_stack((self.X_flat, self.Y_flat, Z))

    def get_mesh_faces(self):
        R, C = self.shape
        faces = []

        for i in range(R - 1):
            for j in range(C - 1):
                k = i * C + j
                faces.append([k, k + 1, k + C])
                faces.append([k + C + 1, k + C, k + 1])

        return np.array(faces, dtype=np.uint32)
