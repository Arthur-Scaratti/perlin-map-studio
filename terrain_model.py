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
        #nova feature --------------- IDW
        self._compute_biome_centers()

        # geração inicial
        self.generate_full_noise()

    def _initialize_default_biomes(self):
        """Cada bioma recebe uma escala entre 0.01 e 0.1."""
        biomes = np.empty(self.BIOME_GRID_SHAPE, dtype=object)

        for r in range(self.BIOME_GRID_SHAPE[0]):
            for c in range(self.BIOME_GRID_SHAPE[1]):
                biomes[r, c] = {
                    "scale": 0.02 + 0.03 * np.random.rand()
                }

        return biomes

    def generate_full_noise(self):
        start = time.time()
        R, C = self.shape

        for i in range(R):
            for j in range(C):

                # escala suavizada IDW
                scale = self.get_smoothed_scale(i, j)

                self.Z_base[i, j] = pnoise2(
                    i * scale,
                    j * scale,
                    octaves=6,
                    persistence=0.6,
                    lacunarity=1.5,
                    repeatx=R,
                    repeaty=C,
                    base=self.GLOBAL_SEED
                )

        # normalização
        mn, mx = self.Z_base.min(), self.Z_base.max()
        self.Z_base = (self.Z_base - mn) / (mx - mn)
        print(f"[TerrainModel] Geração completa ({R}x{C}) em {time.time() - start:.2f}s")


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
    
    def _compute_biome_centers(self):
        """Calcula o centro (x,y) de cada bioma da grade."""
        self.biome_centers = {}

        rows, cols = self.BIOME_GRID_SHAPE
        S = self.BIOME_SIZE

        for r in range(rows):
            for c in range(cols):
                center_x = r * S + S/2
                center_y = c * S + S/2

                self.biome_centers[(r,c)] = (center_x, center_y)

    def get_smoothed_scale(self, x, y, power=1.5):
        """
        Calcula a escala suavizada via Inverse Distance Weighting (IDW).
        x, y = coordenadas do pixel
        power = expoente da distância (2 = natural)
        """

        weights_sum = 0.0
        value_sum = 0.0

        # Itera por todos os biomas
        for (r, c), (cx, cy) in self.biome_centers.items():
            dx = x - cx
            dy = y - cy
            dist_sq = dx*dx + dy*dy

        # Evita divisão por zero (se estiver exatamente no centro)
            if dist_sq < 1e-6:
                return self.biomes_params[r, c]["scale"]

            w = 1.0 / (dist_sq ** (power/2))
            weights_sum += w
            value_sum += w * self.biomes_params[r, c]["scale"]

        return value_sum / weights_sum
