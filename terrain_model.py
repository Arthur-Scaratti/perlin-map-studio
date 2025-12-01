import numpy as np
from noise import pnoise2

class TerrainModel:
    """Responsável por gerar e atualizar os dados da nuvem de pontos."""
    def __init__(self, shape=(100, 100), scale=0.1):
        self.shape = shape
        self.scale = scale
        self.X, self.Y = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]))

        self.Z_base = self._generate_base_noise()

        self.X_flat = self.X.ravel()
        self.Y_flat = self.Y.ravel()

    def _generate_base_noise(self):
        Z = np.zeros(self.shape)
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                Z[i, j] = pnoise2(i * self.scale, j * self.scale, octaves=4)
        return Z

    def get_points_data(self, amplitude):
        Z_scaled = self.Z_base.ravel() * amplitude
        return np.column_stack((self.X_flat, self.Y_flat, Z_scaled))

    def get_mesh_faces(self):
        R, C = self.shape
        faces = []
        for i in range(R - 1):
            for j in range(C - 1):
                k = i * C + j
                tri1 = [k, k + 1, k + C]
                tri2 = [k + C + 1, k + C, k + 1]
                faces.append(tri1)
                faces.append(tri2)
        return np.array(faces, dtype=np.uint32)
