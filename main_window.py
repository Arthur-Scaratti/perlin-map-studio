from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSlider, QLabel, QFileDialog,
    QMessageBox, QPushButton, QGridLayout, QDoubleSpinBox,
    QHBoxLayout, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt

from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas
from setup_form import SetupForm # Importa o novo form

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Studio - Perlin Noise 3D")
        self.setGeometry(100, 100, 1300, 900)

        # Layout Principal Horizontal (Splitter)
        main_layout = QHBoxLayout()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. Painel Esquerdo (ScrollArea para o Form)
        left_panel = QScrollArea()
        left_panel.setWidgetResizable(True)
        left_panel.setMinimumWidth(350)
        
        self.form_widget = SetupForm(on_generate_callback=self.on_generate_request)
        left_panel.setWidget(self.form_widget)
        
        self.splitter.addWidget(left_panel)

        # 2. Painel Direito (Visualização + Controles de Bioma)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Modelo e VisPy
        self.model = TerrainModel() 
        # Nota: O modelo inicia "vazio" ou padrão. Vamos gerar uma vez para não ficar preto.
        
        self.vispy_widget = VisPyCanvas(self.model)
        right_layout.addWidget(self.vispy_widget.native)
        
        # --- Controles Pós-Geração (Biomas e Visualização) ---
        # Slider de Amplitude Visual
        self.pending_amplitude = 10.0
        self.label_altura = QLabel("Amplitude Visual (Z-Scale): 10.0")
        right_layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(150)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        right_layout.addWidget(self.slider)

        # Área de Biomas (Dinâmica)
        self.biome_container = QWidget()
        self.biome_layout = QGridLayout()
        self.biome_container.setLayout(self.biome_layout)
        
        scroll_biomes = QScrollArea()
        scroll_biomes.setWidgetResizable(True)
        scroll_biomes.setWidget(self.biome_container)
        scroll_biomes.setMaximumHeight(200)
        
        right_layout.addWidget(QLabel("Ajuste Fino de Biomas (Pós-Geração):"))
        right_layout.addWidget(scroll_biomes)
        
        # Botão Atualizar Biomas (apenas atualiza o noise atual, não regenera seed/tamanho)
        self.btn_update_biomes = QPushButton("Atualizar Apenas Escalas de Bioma")
        self.btn_update_biomes.clicked.connect(self.on_update_biomes_only)
        right_layout.addWidget(self.btn_update_biomes)

        # Exporter
        self.exporter = HeightmapExporter()
        self.export_button = QPushButton("Exportar Heightmap (PNG 16-bit)")
        self.export_button.clicked.connect(self.export_terrain)
        right_layout.addWidget(self.export_button)

        right_panel.setLayout(right_layout)
        self.splitter.addWidget(right_panel)
        
        # Define proporção do splitter (30% Form, 70% VisPy)
        self.splitter.setSizes([350, 950])

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)

        # Estado para biomas
        self.biome_inputs = []
        
        # Gera o inicial
        self.form_widget.collect_and_emit()

    # ==========================================================
    # Lógica de Geração Completa (Vinda do Form)
    # ==========================================================
    def on_generate_request(self, params):
        """
        Chamado quando o botão 'GERAR MAPA' é clicado.
        Reconfigura o modelo do zero, regenera malhas e noise.
        """
        # 1. Detectar mudança de tamanho para recriar o Canvas se necessário
        # VisPy é chato com mudança de numero de vertices.
        # A maneira mais segura é atualizar o objeto visual com novos faces.
        
        old_shape = self.model.shape
        
        # Gera o terreno
        self.model.configure_and_generate(params)
        
        new_shape = self.model.shape
        
        # Se o tamanho mudou, precisamos avisar o VisPy para pegar novas faces
        if old_shape != new_shape:
            # Atualiza faces no VisPy
            new_faces = self.model.get_mesh_faces()
            self.vispy_widget.faces = new_faces
            # Reseta a camera para caber o novo mapa
            self.vispy_widget.view.camera.set_range(
                x=[0, new_shape[1]],
                y=[0, new_shape[0]],
                z=[-50, 50]
            )

        # Atualiza visualização
        self.vispy_widget.update_visualization(self.pending_amplitude)
        
        # Reconstrói a grade de inputs de bioma na UI
        self.rebuild_biome_grid_ui()
        
        # Salva params atuais para updates parciais
        self.last_params = params

    def rebuild_biome_grid_ui(self):
        """Reconstroi os spinboxes da grade de biomas baseado no tamanho atual."""
        # Limpar layout antigo
        for i in reversed(range(self.biome_layout.count())): 
            self.biome_layout.itemAt(i).widget().setParent(None)
            
        self.biome_inputs = []
        rows, cols = self.model.BIOME_GRID_SHAPE
        
        for r in range(rows):
            row_inputs = []
            for c in range(cols):
                spin = QDoubleSpinBox()
                spin.setDecimals(4)
                spin.setRange(0.0001, 1.0)
                spin.setSingleStep(0.001)
                spin.setValue(self.model.biomes_params[r, c]["scale"])
                # Conecta sinal
                # Usamos lambda com valores padrão para capturar r, c no loop
                spin.valueChanged.connect(lambda val, rr=r, cc=c: self.update_biome_local_param(rr, cc, val))
                
                self.biome_layout.addWidget(spin, r, c)
                row_inputs.append(spin)
            self.biome_inputs.append(row_inputs)

    def update_biome_local_param(self, r, c, val):
        self.model.set_biome_scale(r, c, val)

    def on_update_biomes_only(self):
        """Re-roda apenas a geração de noise usando os params atuais, mas com novas escalas de bioma."""
        if hasattr(self, 'last_params'):
            self.model.configure_and_generate(self.last_params)
            self.vispy_widget.update_visualization(self.pending_amplitude)

    # ==========================================================
    # Outros Callbacks
    # ==========================================================
    def on_amplitude_change(self, value):
        self.pending_amplitude = float(value)
        self.label_altura.setText(f"Amplitude Visual (Z-Scale): {self.pending_amplitude:.1f}")
        self.vispy_widget.update_visualization(self.pending_amplitude)

    def export_terrain(self):
        Z_2D = self.model.Z_base
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Heightmap", "terrain_gen.png", "PNG Files (*.png)")
        if file_path:
            self.exporter.export_heightmap(Z_2D, output_path=file_path)
            QMessageBox.information(self, "Sucesso", f"Salvo em:\n{file_path}")