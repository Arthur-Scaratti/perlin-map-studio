import numpy as np
from noise import pnoise2 
import time
from config import GRID_SIZE, BIOME_SIZE, BIOME_GRID_SHAPE

class TerrainModel:

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

        self._generate_base_height_map() # gera mapa de altura base (baixa frequência)
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
        """
        Gera o ruído final, onde o ruído de detalhe é somado como 
        deslocamento (offset) sobre o mapa de altura base suave.
        """
        start = time.time()
        R, C = self.shape
        
        # Parâmetros de Ponderação (Ajuste esses valores para controlar o resultado)
        # O quão 'montanhoso' ou 'acidentado' o detalhe será
        DETAIL_AMPLITUDE_FACTOR = 1 
        # Esta é a proporção do ruído de detalhe ([-1, 1]) que será somada.
        # Ex: 1 significa que o detalhe pode adicionar ou subtrair até 1 da altura base.

        for i in range(R):
            for j in range(C):
                # 1. Obter a escala do bioma (Ruído de Detalhe)
                biome_r = i // self.BIOME_SIZE
                biome_c = j // self.BIOME_SIZE
                scale_detail = self.biomes_params[biome_r, biome_c]["scale"]

                # 2. Gerar o Ruído de Detalhe (Varia em torno de [-1, 1])
                Z_detail_noise = pnoise2(
                    i * scale_detail, 
                    j * scale_detail,
                    octaves=6,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=R,
                    repeaty=C,
                    base=self.GLOBAL_SEED 
                )
                
                # 3. Obter a Altura Base (já normalizada para [0, 1])
                Z_base_height = self.Z_base_map[i, j]
                
                # 4. Combinação: Soma do Detalhe como um Offset
                # Z_detail_noise * DETAIL_AMPLITUDE_FACTOR (Varia de [-1, 1])
                # É somado à Altura Base (Varia de [0, 1])
                self.Z_base[i, j] = Z_base_height + (Z_detail_noise * DETAIL_AMPLITUDE_FACTOR)

        # 5. Normalização Final ???? nao funcionou muito bem
        # Ela garante que o ponto mais baixo seja 0 e o mais alto seja 1, 
        # preenchendo o espaço de altura disponível.
        #mn, mx = self.Z_base.min(), self.Z_base.max()
        #if mx != mn:
        #    self.Z_base = (self.Z_base - mn) / (mx - mn)
        self.Z_base = np.clip(self.Z_base, 0.0, 1.5)

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
    
    def _generate_base_height_map(self):
        """Gera um mapa de altura base (baixa frequência) para grandes formas do terreno."""
        R, C = self.shape
        self.Z_base_map = np.zeros(self.shape)

        # Scale BEM BAIXA para formas grandes
        BASE_SCALE_FACTOR = 0.005

        for i in range(R):
            for j in range(C):
                self.Z_base_map[i, j] = pnoise2(
                    i * BASE_SCALE_FACTOR,
                    j * BASE_SCALE_FACTOR,
                    octaves=4, # Menos oitavas para ser mais suave
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=R,
                    repeaty=C,
                    base=self.GLOBAL_SEED + 100 # Uma seed diferente para garantir independência
                )
        
        
        # Vou normalizar para [0, 1], o impacto da altura será controlado pela amplitude final.
        mn, mx = self.Z_base_map.min(), self.Z_base_map.max()
        self.Z_base_map = (self.Z_base_map - mn) / (mx - mn)
        
        print("[TerrainModel] Mapa de altura base gerado.")