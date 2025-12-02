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
        self.update_visualization(10)

    def update_visualization(self, amplitude):
        start = time.time()

        points = self.model.get_points_data(amplitude)
        
        # --- LÓGICA DE COR CORRIGIDA (ABSOLUTA) ---
        
        # Descobrir a altura "normalizada" (0 a 1) para pintar corretamente.
        # Como points[:, 2] já está multiplicado pela amplitude, vamos reverter ou usar o Z_base original.
        # O jeito mais fácil é pegar o Z_base original do modelo, que vai de 0 a 1.
        z_raw = self.model.Z_base.ravel() 
        
        # Defina um "Nível do Mar" fixo (ex: 0.4 ou 40%)
        SEA_LEVEL = 0.3
        
        colors = []
        for z in z_raw:
            if z < SEA_LEVEL:
                # É ÁGUA (Azul)
                # Podemos variar o tom de azul baseado na profundidade se quiser
                colors.append([0.0, 0.0, 0.5 + (z * 0.5), 1.0]) 
            else:
                # É TERRA (Degradê Verde -> Marrom -> Branco)
                # Re-normaliza apenas a parte da terra para calcular a cor
                land_norm = (z - SEA_LEVEL) / (1.0 - SEA_LEVEL)
                
                if land_norm < 0.05:
                     # amarelo areia (Beach)
                        colors.append([0.8, 0.7 + (land_norm * 0.3), 0.5, 1.0])
                elif land_norm < 0.5:
                     # Verde (Grass)
                     colors.append([0.2, 0.5 + (land_norm * 0.5), 0.2, 1.0])
                elif land_norm < 0.55:
                     # Marrom/Cinza (Rock)
                     colors.append([0.5, 0.4, 0.3, 1.0])
                else:
                     # Branco (Snow)
                     colors.append([1.0, 1.0, 1.0, 1.0])

        self.mesh.set_data(
            vertices=points,
            faces=self.faces,
            vertex_colors=np.array(colors) # Converter para array numpy
        )

        print(f"[VisPy] Atualização da malha: {time.time() - start:.2f}s")
