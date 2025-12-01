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
            x=[0, model.shape[0]],
            y=[0, model.shape[1]],
            z=[-50, 50]
        )
        self.view.camera.scale_factor = 1000

        self.mesh = visuals.Mesh(parent=self.view.scene, shading="flat")
        self.update_visualization(10)

    def update_visualization(self, amplitude):
        start = time.time()

        points = self.model.get_points_data(amplitude)

        zmin, zmax = points[:, 2].min(), points[:, 2].max()
        if zmax == zmin:
            colors = [[0.5, 0.5, 0.5, 1.0]] * len(points)
        else:
            norm = (points[:, 2] - zmin) / (zmax - zmin)
            colors = [[n * .5, 0.5 + n * .5, 1-n, 1] for n in norm]

        self.mesh.set_data(
            vertices=points,
            faces=self.faces,
            vertex_colors=colors
        )

        print(f"[VisPy] Atualização da malha: {time.time() - start:.2f}s")
