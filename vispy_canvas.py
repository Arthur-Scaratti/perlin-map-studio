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
            x=[0, model.shape[1]],
            y=[0, model.shape[0]],
            z=[-50, 50]
        )
        self.view.camera.scale_factor = 1000

        self.mesh = visuals.Mesh(parent=self.view.scene, shading="flat")
        
        # Configs de biomas (defaults hardcoded, mas agora pode ser sobrescrito)
        self.biome_configs = [
            {'min': 0.0, 'max': 0.35, 'color': [0.0549, 0.1098, 0.2980, 1.0]},  # Sea
            {'min': 0.35, 'max': 0.38, 'color': [0.8314, 0.8000, 0.6471, 1.0]},  # Sand
            {'min': 0.38, 'max': 0.75, 'color': [0.1098, 0.2627, 0.1804, 1.0]},  # Grass
            {'min': 0.75, 'max': 1.5, 'color': [1.0, 1.0, 1.0, 1.0]}   # Snow
        ]
        
        self.update_visualization(150)

    def update_camera(self):
        R, C = self.model.shape
        cx, cy = C / 2, R / 2
        radius = min(R, C) / 2

        self.view.camera.set_range(
            x=[cx - radius, cx + radius],
            y=[cy - radius, cy + radius],
            z=[-50, 50]
        )

    def update_visualization(self, amplitude):
        start = time.time()
        z_raw = self.model.Z_base.ravel()
        n_points = len(z_raw)
    
        colors = np.zeros((n_points, 4), dtype=np.float32)
        colors[:, 3] = 1.0  # Alpha
        
        # Aplicar máscaras dinâmicas baseadas em biome_configs
        for biome in self.biome_configs:
            mask = (z_raw >= biome['min']) & (z_raw < biome['max'])
            colors[mask] = biome['color']
        
        self.mesh.set_data(
            vertices=self.model.get_points_data(amplitude),
            faces=self.faces,
            vertex_colors=colors
        )

        print(f"[VisPy] Atualização da malha: {time.time() - start:.2f}s")