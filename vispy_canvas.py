import numpy as np
from vispy import scene
from vispy.scene import visuals
import time

class VisPyCanvas(scene.SceneCanvas):
    def __init__(self, model):
        scene.SceneCanvas.__init__(self, keys="interactive", size=(800, 800))
        self.unfreeze()

        self.model = model
        self.faces = self.model.get_mesh_faces()

        self.view = self.central_widget.add_view()
        self.view.camera = "turntable"
        self.view.camera.set_range(
            x=[0, model.shape[1]],  # x corresponde a colunas (W)
            y=[0, model.shape[0]],  # y corresponde a linhas (H)
            z=[-50, 50]
        )
        self.view.camera.scale_factor = 1000

        self.mesh = visuals.Mesh(parent=self.view.scene, shading="flat")
        self.update_visualization(150)

    def update_visualization(self, amplitude):
        start = time.time()
        z_raw = self.model.Z_base.ravel()
        n_points = len(z_raw)
    
        # Criar array de cores (Default: Verde)
        colors = np.zeros((n_points, 4), dtype=np.float32)
        colors[:, 3] = 1.0 # Alpha
    
        # Máscaras booleanas (Vetorização)
        sea_mask = z_raw < 0.3
        sand_mask = (z_raw >= 0.3) & (z_raw < 0.35)
        snow_mask = z_raw > 0.8
        grass_mask = ~(sea_mask | sand_mask | snow_mask)

        # Aplicação de cores em bloco
        colors[sea_mask] = [0.0, 0.3, 0.6, 1.0]   # Azul
        colors[sand_mask] = [0.8, 0.7, 0.4, 1.0]  # Areia
        colors[grass_mask] = [0.2, 0.5, 0.2, 1.0] # Verde
        colors[snow_mask] = [1.0, 1.0, 1.0, 1.0]  # Branco
        self.mesh.set_data(
            vertices=self.model.get_points_data(amplitude),
            faces=self.faces,
            vertex_colors=colors
        )

        print(f"[VisPy] Atualização da malha: {time.time() - start:.2f}s")
