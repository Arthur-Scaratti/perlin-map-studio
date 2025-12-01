import numpy as np
from vispy import scene
from vispy.scene import visuals

class VisPyCanvas(scene.SceneCanvas):
    """Componente VisPy para renderização 3D."""
    def __init__(self, model):
        super().__init__(keys='interactive', size=(600, 600))
        self.unfreeze()

        self.model = model
        self.faces = self.model.get_mesh_faces()

        self.view = self.central_widget.add_view()
        self.view.camera = 'turntable'

        self.mesh = visuals.Mesh(parent=self.view.scene, shading='flat')
        self.update_visualization(1.0)

        scene.visuals.GridLines(parent=self.view.scene)

    def update_visualization(self, amplitude):
        points = self.model.get_points_data(amplitude)

        z_min, z_max = points[:, 2].min(), points[:, 2].max()
        if z_max == z_min:
            colors = np.array([[0.5, 0.5, 0.5, 1.0]] * len(points))
        else:
            norm_z = (points[:, 2] - z_min) / (z_max - z_min)
            colors = np.zeros((len(points), 4))
            colors[:, 1] = norm_z
            colors[:, 2] = 1 - norm_z
            colors[:, 3] = 1.0

        self.mesh.set_data(
            vertices=points,
            faces=self.faces,
            vertex_colors=colors
        )
        self.view.camera.set_range()
