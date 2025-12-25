import numpy as np
import time
from config import DEFAULT_GRID_SIZE
from mask_utils import get_continent_centers, generate_multi_point_mask
from numba import jit, prange, njit

class TerrainModel:
    def __init__(self):
        self.shape = (DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE)
        self.upper_scale = 0.011 
        
        self.Z_base = np.zeros(self.shape, dtype=np.float32)
        self.Z_base_map = np.zeros(self.shape, dtype=np.float32)
        
        self.X, self.Y = None, None
        self.X_flat, self.Y_flat = None, None

        self.mask = None
        
        self.update_grid_size(DEFAULT_GRID_SIZE)

    def update_grid_size(self, new_size):
        self.shape = (new_size, new_size)
        self.X, self.Y = np.meshgrid(
            np.arange(self.shape[0]),
            np.arange(self.shape[1])
        )
        self.X_flat = self.X.ravel().astype(np.int32)
        self.Y_flat = self.Y.ravel().astype(np.int32)
        self.Z_base = np.zeros(self.shape, dtype=np.float32)
        self.mask = np.ones(self.shape, dtype=bool) 

    def get_mesh_faces(self, step=1):
        start = time.time()
        
        R_orig, C_orig = self.shape
        
        # Slicing nas dimensões
        y_slice = slice(0, R_orig, step)
        x_slice = slice(0, C_orig, step)
        
        # A máscara fatiada
        mask_view = self.mask[y_slice, x_slice]
        
        # Novas dimensões da view
        R, C = mask_view.shape
        
        indices = np.arange(R * C, dtype=np.uint32).reshape(R, C)

        v1 = indices[:-1, :-1].ravel()
        v2 = indices[:-1, 1:].ravel()
        v3 = indices[1:, :-1].ravel()
        v4 = indices[1:, 1:].ravel()

        f1 = np.column_stack((v1, v2, v3))
        f2 = np.column_stack((v4, v3, v2))
        
        # =========================
        # MÁSCARAS DE FACE (vetorizadas)
        # =========================
        # Usamos a mask_view (reduzida) aqui
        m = mask_view

        mask_f1 = (
            m[:-1, :-1] &
            m[:-1, 1:] &
            m[1:, :-1]
        ).ravel()

        mask_f2 = (
            m[1:, 1:] &
            m[1:, :-1] &
            m[:-1, 1:]
        ).ravel()

        f1 = f1[mask_f1]
        f2 = f2[mask_f2]

        print(f"[Model] get_mesh_faces (step={step}): {time.time() - start:.4f}s")
        return np.vstack((f1, f2)).astype(np.uint32)

    def get_points_data(self, amplitude, step=1):
        # Fatia o Z e os grids X/Y
        z_view = self.Z_base[::step, ::step]
        x_view = self.X[::step, ::step]
        y_view = self.Y[::step, ::step]
        
        # Ravel
        z_flat = z_view.ravel() * (amplitude / 10.0)
        x_flat = x_view.ravel()
        y_flat = y_view.ravel()
        
        return np.column_stack((x_flat, y_flat, z_flat))
    
    # Adicione este helper para pegar o Z cru reduzido (usado para colorir)
    def get_z_flat(self, step=1):
        return self.Z_base[::step, ::step].ravel()
    
    def generate_fbm_noise(self, X, Y, scale, octaves, persistence, lacunarity, base, repeatx=None, repeaty=None):
        height, width = X.shape

        ps = []
        for o in range(octaves):
            np.random.seed(base + o)
            p = np.arange(256, dtype=np.int32)
            np.random.shuffle(p)
            p = np.concatenate((p, p))
            ps.append(p)

        @njit
        def fade(t):
            return 6 * t**5 - 15 * t**4 + 10 * t**3

        @njit
        def lerp(a, b, x):
            return a + x * (b - a)

        @njit
        def grad(hash_code, x, y):
            h = hash_code % 4
            if h == 0:
                return 0.70710678118 * (x + y)
            elif h == 1:
                return 0.70710678118 * (-x + y)
            elif h == 2:
                return 0.70710678118 * (x - y)
            else:
                return 0.70710678118 * (-x - y)

        @njit
        def perlin_scalar(x, y, p):
            if repeatx is not None:
                x = x % repeatx
            if repeaty is not None:
                y = y % repeaty

            xi = int(x) & 255
            yi = int(y) & 255
            xf = x - int(x)
            yf = y - int(y)

            u = fade(xf)
            v = fade(yf)

            aa = p[p[xi] + yi]
            ab = p[p[xi] + yi + 1]
            ba = p[p[xi + 1] + yi]
            bb = p[p[xi + 1] + yi + 1]

            x1 = lerp(grad(aa, xf, yf), grad(ba, xf - 1, yf), u)
            x2 = lerp(grad(ab, xf, yf - 1), grad(bb, xf - 1, yf - 1), u)

            return lerp(x1, x2, v) * np.sqrt(2)

        @njit(parallel=True)
        def compute_noise(ps, X, Y, scale, octaves, persistence, lacunarity, repeatx, repeaty, height, width):
            noise_grid = np.zeros((height, width), dtype=np.float32)
            
            for o in prange(octaves):
                freq = scale * (lacunarity ** o)
                amp = persistence ** o
                
                p = ps[o]
                
                for i in prange(height):
                    for j in prange(width):
                        nx = X[i, j] * freq
                        ny = Y[i, j] * freq
                        val = perlin_scalar(nx, ny, p)
                        noise_grid[i, j] += val * amp
            
            return noise_grid

        noise_grid = compute_noise(ps, X, Y, scale, octaves, persistence, lacunarity, repeatx, repeaty, height, width)
        
        return noise_grid

    def configure_and_generate(self, params):
        start_total = time.time()
        
        shape = params.get("shape", "round")
        shape_params = params.get("shape_params", {})

        # =========================
        # SHAPE CONFIG
        # =========================

        if shape == "round":
            radius = int(shape_params.get("radius", 513))
            dia = (radius * 2) - 1
            if self.shape != (dia, dia):
                self.update_grid_size(dia)

            cx = cy = radius
            dist = np.sqrt((self.X - cx) ** 2 + (self.Y - cy) ** 2).astype(np.float32)
            self.mask = dist <= radius
            
    
            self.upper_scale = params['upper_scale']
            
            if params['use_base_map']:
                self.Z_base_map = self.generate_fbm_noise(
                    self.X, self.Y, params['base_scale'], params['octaves_base'],
                    params.get('base_persistence', 0.6), params.get('base_lacunarity', 2.0),
                    params['seed'] + params['seed_adder']
                )
                z_min, z_max = self.Z_base_map.min(), self.Z_base_map.max()
                if z_max > z_min:
                    self.Z_base_map = (self.Z_base_map - z_min) / (z_max - z_min)

            noise_detail = self.generate_fbm_noise(
                self.X, self.Y, self.upper_scale, params['octaves'],
                params.get('persistence', 0.5), params.get('lacunarity', 2.1),
                params['seed']
            )

            if params['use_base_map']:
                self.Z_base = self.Z_base_map + (noise_detail * params['amplitude_factor'])
            else:
                self.Z_base = (noise_detail + 1) / 2.0

            # --- LÓGICA DE ISOLAMENTO DE CONTINENTES ---
            num_continents = params.get("continents_count", 5)
            cont_size = params.get("continent_size", 0.06)

            centers = get_continent_centers(num_continents)
            influence_mask = generate_multi_point_mask(
                self.shape, 
                centers, 
                size_factor=cont_size,
                softness=0.15         
            )

            if params['use_base_map']:
                self.Z_base = (self.Z_base_map * influence_mask) + (noise_detail * params['amplitude_factor'] * influence_mask)
            else:
                self.Z_base = ((noise_detail + 1) / 2.0) * influence_mask

            
            self.Z_base = np.clip(self.Z_base, 0.0, params['clip_max'])
            
        elif shape == "sphere":
            self.upper_scale = params['upper_scale'] 
            
            height = shape_params.get("height", 500)
            width = height * 2

            if self.shape != (height, width): 
                self.shape = (height, width)
                self.X, self.Y = np.meshgrid(np.arange(width), np.arange(height))
                self.X_flat = self.X.ravel()
                self.Y_flat = self.Y.ravel()
                self.Z_base = np.zeros(self.shape)
                self.mask = np.ones(self.shape, dtype=bool) 

        
            repeat_x = width
            repeat_y = height 
            
            if params['use_base_map']:
                self.Z_base_map = self.generate_fbm_noise(
                    self.X, self.Y, params['base_scale'], params['octaves_base'],
                    params.get('base_persistence', 0.6), params.get('base_lacunarity', 2.0),
                    params['seed'] + params['seed_adder'], repeatx=repeat_x, repeaty=repeat_y
                )
                z_min, z_max = self.Z_base_map.min(), self.Z_base_map.max()
                if z_max > z_min:
                    self.Z_base_map = (self.Z_base_map - z_min) / (z_max - z_min)

            noise_detail = self.generate_fbm_noise(
                self.X, self.Y, self.upper_scale, params['octaves'],
                params.get('persistence', 0.5), params.get('lacunarity', 2.1),
                params['seed'], repeatx=repeat_x, repeaty=repeat_y
            )

            if params['use_base_map']:
                self.Z_base = self.Z_base_map + (noise_detail * params['amplitude_factor'])
            else:
                self.Z_base = (noise_detail + 1) / 2.0

            self.Z_base = np.clip(self.Z_base, 0.0, params['clip_max'])
            self.mask[:] = True  
        
        else:  # square
            if self.shape[0] != shape_params.get("side", 500):
                self.update_grid_size(shape_params.get("side", 500))
            self.mask[:] = True
        
            self.upper_scale = params['upper_scale']
            # =========================
            # BASE MAP
            # =========================
            if params['use_base_map']:
                self.Z_base_map = self.generate_fbm_noise(
                    self.X, self.Y, params['base_scale'], params['octaves_base'],
                    params.get('base_persistence', 0.6), params.get('base_lacunarity', 2.0),
                    params['seed'] + params['seed_adder']
                )
                z_min, z_max = self.Z_base_map.min(), self.Z_base_map.max()
                if z_max > z_min:
                    self.Z_base_map = (self.Z_base_map - z_min) / (z_max - z_min)

            noise_detail = self.generate_fbm_noise(
                self.X, self.Y, self.upper_scale, params['octaves'],
                params.get('persistence', 0.5), params.get('lacunarity', 2.1),
                params['seed']
            )

            if params['use_base_map']:
                self.Z_base = self.Z_base_map + (noise_detail * params['amplitude_factor'])
            else:
                self.Z_base = (noise_detail + 1) / 2.0

            self.Z_base = np.clip(self.Z_base, 0.0, params['clip_max'])

        # =========================
        # APPLY MASK (ROUND)
        # =========================
        self.Z_base[~self.mask] = 0.0

        print(f"[Model] Gerado em: {time.time() - start_total:.4f}s")