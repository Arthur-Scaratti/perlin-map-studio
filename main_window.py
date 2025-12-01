from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSlider, QLabel, QFileDialog,
    QMessageBox, QPushButton, QGridLayout, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from config import BIOME_GRID_H, BIOME_GRID_W
from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas


class MainWindow(QWidget):
    """Janela principal integrando VisPy, biomas e PyQt."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("Mapa 3D Interativo com Ruído Perlin")
        self.setGeometry(100, 100, 900, 900)

        # --------------------------
        # Modelo de terreno
        # --------------------------
        self.model = TerrainModel()
        self.vispy_widget = VisPyCanvas(self.model)

        layout.addWidget(self.vispy_widget.native)

        # --------------------------
        # Botão de exportação
        # --------------------------
        self.exporter = HeightmapExporter()

        self.export_button = QPushButton("Exportar Heightmap (PNG 16-bit)")
        self.export_button.clicked.connect(self.export_terrain)
        layout.addWidget(self.export_button)

        # --------------------------
        # Slider de amplitude
        # --------------------------
        self.pending_amplitude = 10.0

        self.label_altura = QLabel("Amplitude da Altura: 10.0")
        layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        layout.addWidget(self.slider)

        # --------------------------
        # Grade de escalas de Biomas
        # --------------------------
        self.pending_biomes = [
            [self.model.biomes_params[r, c]["scale"]
             for c in range(BIOME_GRID_W)]
            for r in range(BIOME_GRID_H)
        ]

        grid_label = QLabel("Escala dos Biomas (8x8):")
        layout.addWidget(grid_label)

        biome_grid_widget = QWidget()
        biome_grid_layout = QGridLayout()

        self.biome_inputs = []

        for r in range(BIOME_GRID_H):
            row_inputs = []
            for c in range(BIOME_GRID_W):
                spin = QDoubleSpinBox()
                spin.setDecimals(4)
                spin.setMinimum(0.001)
                spin.setMaximum(1.0)
                spin.setSingleStep(0.001)
                spin.setValue(self.model.biomes_params[r, c]["scale"])

                # capturar mudança pendente
                spin.valueChanged.connect(
                    lambda v, rr=r, cc=c: self.on_biome_scale_change(rr, cc, v)
                )

                biome_grid_layout.addWidget(spin, r, c)
                row_inputs.append(spin)

            self.biome_inputs.append(row_inputs)

        biome_grid_widget.setLayout(biome_grid_layout)
        layout.addWidget(biome_grid_widget)

        # --------------------------
        # Botão Aplicar
        # --------------------------
        self.apply_button = QPushButton("Atualizar mapa")
        self.apply_button.clicked.connect(self.apply_updates)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    # ----------------------------------------------------------------------
    # EVENTOS
    # ----------------------------------------------------------------------
    def on_amplitude_change(self, value):
        self.pending_amplitude = float(value)
        self.label_altura.setText(f"Amplitude da Altura: {self.pending_amplitude:.1f}")

    def on_biome_scale_change(self, r, c, value):
        """Armazena valor pendente sem atualizar a malha."""
        self.pending_biomes[r][c] = float(value)


    def apply_updates(self):
        for r in range(BIOME_GRID_H):
            for c in range(BIOME_GRID_W):
                self.model.biomes_params[r, c]["scale"] = self.pending_biomes[r][c]

        self.model.generate_full_noise()
        self.vispy_widget.update_visualization(self.pending_amplitude)


    def export_terrain(self):
        Z_2D = self.model.Z_base

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Heightmap",
            "terrain_biome_800x800.png",
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
