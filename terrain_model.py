import numpy as np
from noise import pnoise2 
import time
from config import DEFAULT_GRID_SIZE

class TerrainModel:
    def __init__(self):
        self.shape = (DEFAULT_GRID_SIZE, DEFAULT_GRID_SIZE)
        self.detail_scale = 0.01 
        
        self.Z_base = None
        self.Z_base_map = None
        
        self.X, self.Y = None, None
        self.X_flat, self.Y_flat = None, None

        self.mask = None  # <<< NOVO
        
        self.update_grid_size(DEFAULT_GRID_SIZE)

    def update_grid_size(self, new_size):
        self.shape = (new_size, new_size)
        self.X, self.Y = np.meshgrid(
            np.arange(self.shape[0]),
            np.arange(self.shape[1])
        )
        self.X_flat = self.X.ravel()
        self.Y_flat = self.Y.ravel()
        self.Z_base = np.zeros(self.shape)
        self.mask = np.ones(self.shape, dtype=bool)  # <<< NOVO

    def get_mesh_faces(self):
        R, C = self.shape
        indices = np.arange(R * C).reshape(R, C)

        # vértices base (igual ao original)
        v1 = indices[:-1, :-1].ravel()
        v2 = indices[:-1, 1:].ravel()
        v3 = indices[1:, :-1].ravel()
        v4 = indices[1:, 1:].ravel()

        f1 = np.column_stack((v1, v2, v3))
        f2 = np.column_stack((v4, v3, v2))
    # =========================
    # MÁSCARAS DE FACE (vetorizadas) NOVO
    # =========================
        m = self.mask

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

        return np.vstack((f1, f2)).astype(np.uint32)

    def get_points_data(self, amplitude):
        Z = self.Z_base.ravel() * (amplitude / 10.0)
        return np.column_stack((self.X_flat, self.Y_flat, Z))

    def configure_and_generate(self, params):
        start_total = time.time()
        
        shape = params.get("shape", "square")
        shape_params = params.get("shape_params", {})

        # =========================
        # SHAPE CONFIG
        # =========================
        if shape == "round":
            radius = int(shape_params.get("radius", params["map_size"] // 2))
            dia = radius * 2
            if self.shape != (dia, dia):
                self.update_grid_size(dia)

            cx = cy = radius
            dist = np.sqrt((self.X - cx) ** 2 + (self.Y - cy) ** 2)
            self.mask = dist <= radius

        else:
            if self.shape[0] != params["map_size"]:
                self.update_grid_size(params["map_size"])
            self.mask[:] = True
        
        self.detail_scale = params['detail_scale']
        vnoise = np.vectorize(pnoise2)
        # =========================
        # BASE MAP
        # =========================
        if params['use_base_map']:
            self.Z_base_map = vnoise(
                self.X * params['base_scale'], 
                self.Y * params['base_scale'], 
                octaves=params['octaves_base'], 
                base=params['seed'] + params['seed_adder']
            )
            z_min, z_max = self.Z_base_map.min(), self.Z_base_map.max()
            if z_max > z_min:
                self.Z_base_map = (self.Z_base_map - z_min) / (z_max - z_min)

        noise_detail = vnoise(
            self.X * self.detail_scale, 
            self.Y * self.detail_scale, 
            octaves=params['octaves'], 
            base=params['seed']
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