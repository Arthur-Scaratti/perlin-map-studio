from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QFileDialog, QMessageBox, QPushButton
from PyQt6.QtCore import Qt

from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas

class MainWindow(QWidget):
    """Janela principal integrando VisPy e PyQt."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("Mapa 3D Interativo com Ruído Perlin")
        self.setGeometry(100, 100, 800, 700)
    
        self.exporter = HeightmapExporter()
        self.model = TerrainModel()
        self.vispy_widget = VisPyCanvas(self.model)

        layout.addWidget(self.vispy_widget.native)

        self.export_button = QPushButton("Exportar Heightmap (16-bit)")
        self.export_button.clicked.connect(self.export_terrain)
        layout.addWidget(self.export_button)

        self.label_altura = QLabel("Amplitude da Altura: 10.0")
        layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self.update_amplitude)
        layout.addWidget(self.slider)

        self.setLayout(layout)

    def update_amplitude(self, value):
        amplitude = float(value)
        self.label_altura.setText(f"Amplitude da Altura: {amplitude:.1f}")
        self.vispy_widget.update_visualization(amplitude)

    def export_terrain(self):
        """Exporta o Heightmap atual, usando QFileDialog."""
        amplitude_atual = self.slider.value()
        Z_2D = self.model.Z_base

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Heightmap",
            "terrain_biome.png",
            "PNG Files (*.png)"
        )

        if file_path:
            self.exporter.export_heightmap(Z_2D, output_path=file_path)
            QMessageBox.information(
                self,
            "Exportação Concluída",
            f"O Heightmap foi salvo em:\n{file_path}",
            QMessageBox.StandardButton.Ok
        )