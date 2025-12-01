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

        self.model = TerrainModel()
        self.vispy_widget = VisPyCanvas(self.model)

        layout.addWidget(self.vispy_widget.native)

        # --- Botão de exportação ---
        self.export_button = QPushButton("Exportar Heightmap (PNG 16-bit)")
        self.export_button.clicked.connect(self.export_terrain)
        layout.addWidget(self.export_button)

        # --- Slider de amplitude (não atualiza mais automaticamente) ---
        self.label_altura = QLabel("Amplitude da Altura: 10.0")
        layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        layout.addWidget(self.slider)

        # --- novo botão: Atualizar Mapa ---
        self.apply_button = QPushButton("Atualizar mapa")
        self.apply_button.clicked.connect(self.apply_updates)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

        # estado interno
        self.pending_amplitude = 10.0

        # exporter
        self.exporter = HeightmapExporter()


    def on_amplitude_change(self, value):
        self.pending_amplitude = float(value)
        self.label_altura.setText(f"Amplitude da Altura: {self.pending_amplitude:.1f}")


    def apply_updates(self):
        self.model.generate_full_noise()
        self.vispy_widget.update_visualization(self.pending_amplitude)

    # ===========================================================
    # Exportação
    # ===========================================================
    def export_terrain(self):
        Z_2D = self.model.Z_base

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Heightmap",
            "terrain_biome_1000x1000.png",
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
