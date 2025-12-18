from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSlider, QLabel, QFileDialog,
    QMessageBox, QPushButton, QHBoxLayout, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt

from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas
from setup_form import SetupForm

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Studio - Perlin Noise 3D")
        self.setGeometry(100, 100, 1300, 900)

        main_layout = QHBoxLayout()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QScrollArea()
        left_panel.setWidgetResizable(True)
        left_panel.setMinimumWidth(350)
        
        self.form_widget = SetupForm(on_generate_callback=self.on_generate_request)
        left_panel.setWidget(self.form_widget)
        
        self.splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.model = TerrainModel() 
        
        self.vispy_widget = VisPyCanvas(self.model)
        right_layout.addWidget(self.vispy_widget.native)
        
        self.pending_amplitude = 10.0
        self.label_altura = QLabel("Amplitude Visual (Z-Scale): 10.0")
        right_layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(150)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        right_layout.addWidget(self.slider)
        
        self.exporter = HeightmapExporter()
        self.export_button = QPushButton("Exportar Heightmap (PNG 16-bit)")
        self.export_button.clicked.connect(self.export_terrain)
        right_layout.addWidget(self.export_button)

        right_panel.setLayout(right_layout)
        self.splitter.addWidget(right_panel)
        
        self.splitter.setSizes([350, 950])

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)
        
        self.form_widget.collect_and_emit()

    def on_generate_request(self, params):
        old_shape = self.model.shape
        
        self.model.configure_and_generate(params)
        
        new_shape = self.model.shape
        
        if old_shape != new_shape:
            new_faces = self.model.get_mesh_faces()
            self.vispy_widget.faces = new_faces
            self.vispy_widget.view.camera.set_range(
                x=[0, new_shape[1]],
                y=[0, new_shape[0]],
                z=[-50, 50]
            )

        self.vispy_widget.update_visualization(self.pending_amplitude)
        
        self.last_params = params

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