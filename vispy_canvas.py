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
        
        # Configurações padrão de cores
        self.color_configs = [
            {'min': 0.0, 'max': 0.35, 'color': [0.0549, 0.1098, 0.2980, 1.0]},  # Sea
            {'min': 0.35, 'max': 0.38, 'color': [0.8314, 0.8000, 0.6471, 1.0]},  # Sand
            {'min': 0.38, 'max': 0.75, 'color': [0.1098, 0.2627, 0.1804, 1.0]},  # Grass
            {'min': 0.75, 'max': 1.5, 'color': [1.0, 1.0, 1.0, 1.0]}   # Snow
        ]

        self.current_step = 1
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
        
        total_points = self.model.shape[0] * self.model.shape[1]
        
        if total_points > 64_000_000:  # Acima de 8000x8000
            step = 16 # Reduz 256x
        elif total_points > 16_000_000:   # Acima de 4000x4000
            step = 8 # Reduz 64x
        elif total_points > 4_000_000:  # Acima de 2000x2000
            step = 4 # Reduz 16x
        elif total_points > 1_000_000:  # Acima de 1000x1000
            step = 2 # Reduz 4x
        else:
            step = 1 # Full
        print(f"[VisPy] Renderizando com Downsample Step: {step} (Orig: {self.model.shape})")
        
        need_new_faces = (step != self.current_step) or (not hasattr(self, 'faces'))
        self.faces = self.model.get_mesh_faces(step=step)
        self.current_step = step


        points = self.model.get_points_data(amplitude, step=step)
        z_raw = self.model.get_z_flat(step=step)

        n_points = len(z_raw)
        colors = np.zeros((n_points, 4), dtype=np.float32)
        colors[:, 3] = 1.0
        
        for biome in self.color_configs:
            mask = (z_raw >= biome['min']) & (z_raw < biome['max'])
            colors[mask] = biome['color']
        
        self.mesh.set_data(
            vertices=points,
            faces=self.faces,
            vertex_colors=colors
        )

        print(f"[VisPy] Atualização da malha concluída: {time.time() - start:.4f}s")