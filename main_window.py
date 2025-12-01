from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel
from PyQt6.QtCore import Qt

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
