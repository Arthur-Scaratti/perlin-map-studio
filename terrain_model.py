import numpy as np
from noise import pnoise2 
import time
from config import DEFAULT_GRID_SIZE, DEFAULT_BIOME_SIZE

class TerrainModel:
    def __init__(self):
        # Inicializa com padrões, mas é sobrescrito pelo Form
        self.shape = (DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE)
        self.BIOME_SIZE = DEFAULT_BIOME_SIZE
        
        # Estado interno
        self.Z_base = None
        self.Z_base_map = None
        self.biomes_params = None
        
        # Inicializa malhas vazias
        self.X, self.Y = None, None
        
        self.X_flat, self.Y_flat = None, None
        
        # Cria a estrutura inicial padrão
        self.update_grid_size(DEFAULT_GRID_SIZE)

    def update_grid_size(self, new_size):
        self.shape = (new_size, new_size)
        # Recalcula quantas células de bioma cabem
        rows = new_size // self.BIOME_SIZE
        cols = new_size // self.BIOME_SIZE
        # Garante pelo menos 1 bioma
        rows = max(1, rows)
        cols = max(1, cols)
        self.BIOME_GRID_SHAPE = (rows, cols)
        # Recria Malhas de coordenadas
        self.X, self.Y = np.meshgrid(
            np.arange(self.shape[0]),
            np.arange(self.shape[1])
        )
        self.X_flat = self.X.ravel()
        self.Y_flat = self.Y.ravel()
        self.Z_base = np.zeros(self.shape)
        
        # Reinicia biomas para o novo tamanho
        self._initialize_default_biomes()

    def set_biome_scale(self, r, c, value):
        if 0 <= r < self.BIOME_GRID_SHAPE[0] and 0 <= c < self.BIOME_GRID_SHAPE[1]:
            self.biomes_params[r, c]["scale"] = float(value)

    def _initialize_default_biomes(self):
        self.biomes_params = np.empty(self.BIOME_GRID_SHAPE, dtype=object)
        for r in range(self.BIOME_GRID_SHAPE[0]):
            for c in range(self.BIOME_GRID_SHAPE[1]):
                self.biomes_params[r, c] = {"scale": 0.01 + 0.01 * np.random.rand()}

    def get_mesh_faces(self):
        R, C = self.shape
        indices = np.arange(R * C).reshape(R, C)
        # Seleciono os vértices dos cantos de cada quadrado do grid
        v1 = indices[:-1, :-1].ravel() # Superior Esquerdo
        v2 = indices[:-1, 1:].ravel()  # Superior Direito
        v3 = indices[1:, :-1].ravel()  # Inferior Esquerdo
        v4 = indices[1:, 1:].ravel()   # Inferior Direito
    
        # Triângulo 1: (v1, v2, v3) | Triângulo 2: (v4, v3, v2)
        f1 = np.column_stack((v1, v2, v3))
        f2 = np.column_stack((v4, v3, v2))

        return np.vstack((f1, f2)).astype(np.uint32)

    def get_points_data(self, amplitude):
        Z = self.Z_base.ravel() * (amplitude / 10.0)
        return np.column_stack((self.X_flat, self.Y_flat, Z))

    # =========================================================================
    # Lógica Principal de Geração Controlada
    # =========================================================================
    
    def configure_and_generate(self, params):
        start_total = time.time()
        
        # 1. Ajuste de tamanho
        if self.shape[0] != params['map_size']:
            self.update_grid_size(params['map_size'])
        
        # Em vez de calcular no loop, cria um mapa de escalas
        scales_grid = np.zeros(self.shape)
        for r in range(self.BIOME_GRID_SHAPE[0]):
            for c in range(self.BIOME_GRID_SHAPE[1]):
                s_val = self.biomes_params[r, c]["scale"]
                r0, r1 = r * self.BIOME_SIZE, (r + 1) * self.BIOME_SIZE
                c0, c1 = c * self.BIOME_SIZE, (c + 1) * self.BIOME_SIZE
                scales_grid[r0:r1, c0:c1] = s_val

        # Vetorizar a função pnoise2
        vnoise = np.vectorize(pnoise2)

        # Gera o Base Map
        if params['use_base_map']:
            self.Z_base_map = vnoise(
                self.X * params['base_scale'], 
                self.Y * params['base_scale'], 
                octaves=params['octaves_base'], 
                base=params['seed'] + params['seed_adder']
            )
            # Normalização
            z_min, z_max = self.Z_base_map.min(), self.Z_base_map.max()
            if z_max > z_min:
                self.Z_base_map = (self.Z_base_map - z_min) / (z_max - z_min)

        # Gerar o ruído fino baseado no bioma
        noise_detail = vnoise(
            self.X * scales_grid, 
            self.Y * scales_grid, 
            octaves=params['octaves'], 
            base=params['seed']
        )

        # Combinação final
        if params['use_base_map']:
            self.Z_base = self.Z_base_map + (noise_detail * params['amplitude_factor'])
        else:
            self.Z_base = (noise_detail + 1) / 2.0

        self.Z_base = np.clip(self.Z_base, 0.0, params['clip_max'])
        print(f"[Model] Gerado em: {time.time() - start_total:.4f}s")