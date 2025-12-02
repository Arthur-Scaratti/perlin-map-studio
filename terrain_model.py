import numpy as np
from noise import pnoise2 
import time
from config import DEFAULT_GRID_SIZE, DEFAULT_BIOME_SIZE

class TerrainModel:
    def __init__(self):
        # Inicializa com padrões, mas será sobrescrito pelo Form
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
        """Reconstroi as malhas X, Y e o Grid de Biomas se o tamanho mudar."""
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

    def _initialize_default_biomes(self):
        """Reinicia a matriz de biomas com escalas aleatórias."""
        self.biomes_params = np.empty(self.BIOME_GRID_SHAPE, dtype=object)
        for r in range(self.BIOME_GRID_SHAPE[0]):
            for c in range(self.BIOME_GRID_SHAPE[1]):
                self.biomes_params[r, c] = {
                    "scale": 0.01 + 0.01 * np.random.rand()
                }

    def set_biome_scale(self, r, c, value):
        if 0 <= r < self.BIOME_GRID_SHAPE[0] and 0 <= c < self.BIOME_GRID_SHAPE[1]:
            self.biomes_params[r, c]["scale"] = float(value)

    def get_mesh_faces(self):
        """Gera os índices das faces (triângulos) para o VisPy."""
        R, C = self.shape
        faces = []
        for i in range(R - 1):
            for j in range(C - 1):
                k = i * C + j
                faces.append([k, k + 1, k + C])
                faces.append([k + C + 1, k + C, k + 1])
        return np.array(faces, dtype=np.uint32)

    def get_points_data(self, amplitude):
        if self.Z_base is None: return None
        Z = self.Z_base.ravel() * (amplitude / 10.0)
        return np.column_stack((self.X_flat, self.Y_flat, Z))

    # =========================================================================
    # Lógica Principal de Geração Controlada
    # =========================================================================
    def configure_and_generate(self, params):
        """
        Recebe um dicionário 'params' com todas as configurações da UI.
        """
        start_total = time.time()
        
        # 1. Verificar se precisa redimensionar o mapa
        current_size = self.shape[0]
        target_size = params['map_size']
        
        if current_size != target_size:
            print(f"[Model] Redimensionando de {current_size} para {target_size}...")
            self.update_grid_size(target_size)
        
        # 2. Extrair parâmetros
        seed = params['seed']
        octaves_detail = params['octaves']
        
        use_base_map = params['use_base_map']
        
        # Parâmetros Base Map
        base_scale = params.get('base_scale', 0.005)
        seed_adder = params.get('seed_adder', 100)
        amplitude_factor = params.get('amplitude_factor', 0.5)
        clip_max = params.get('clip_max', 1.5)
        octaves_base = params.get('octaves_base', 4)

        # 3. Gerar Base Height Map (Se habilitado)
        self.Z_base_map = np.zeros(self.shape)
        if use_base_map:
            self._generate_base_height_map(seed + seed_adder, base_scale, octaves_base)

        # 4. Loop Principal
        start_loop = time.time()
        R, C = self.shape
        
        for i in range(R):
            for j in range(C):
                # Proteção de índice caso o bioma seja menor que o grid por arredondamento
                b_r = min(i // self.BIOME_SIZE, self.BIOME_GRID_SHAPE[0]-1)
                b_c = min(j // self.BIOME_SIZE, self.BIOME_GRID_SHAPE[1]-1)
                
                scale_detail = self.biomes_params[b_r, b_c]["scale"]
                
                noise_detail = pnoise2(
                    i * scale_detail,
                    j * scale_detail,
                    octaves=octaves_detail,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=R,
                    repeaty=C,
                    base=seed
                )
                
                # Combinação
                if use_base_map:
                    base_h = self.Z_base_map[i, j]
                    # Soma ponderada
                    val = base_h + (noise_detail * amplitude_factor)
                else:
                    # Se não usar base map, usa apenas o noise normalizado para 0..1 (aprox)
                    val = (noise_detail + 1) / 2.0

                self.Z_base[i, j] = val

        # 5. Clip Final (Apenas se usar base map)
        self.Z_base = np.clip(self.Z_base, 0.0, clip_max)

        print(f"[Model] Geração completa em {time.time() - start_total:.2f}s")

    def _generate_base_height_map(self, seed_base, scale, octaves):
        """Gera o mapa de baixa frequência."""
        R, C = self.shape
        print(f"[Model] Gerando Base Height Map (Scale: {scale}, Octaves: {octaves})...")
        
        for i in range(R):
            for j in range(C):
                val = pnoise2(
                    i * scale,
                    j * scale,
                    octaves=octaves,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=R,
                    repeaty=C,
                    base=seed_base
                )
                self.Z_base_map[i, j] = val
        
        # Normaliza base map para 0..1
        mn, mx = self.Z_base_map.min(), self.Z_base_map.max()
        if mx != mn:
            self.Z_base_map = (self.Z_base_map - mn) / (mx - mn)