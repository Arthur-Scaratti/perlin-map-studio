from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QSlider, QLabel, QFileDialog,
    QMessageBox, QPushButton, QMenuBar, QDockWidget, QWidget,
    QTabWidget, QColorDialog, QHBoxLayout, QToolButton,
    QDoubleSpinBox
)
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize

from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas
from setup_form import SetupForm


class ColorEditorWidget(QWidget):
    def __init__(self, main_window, vispy_widget):
        super().__init__()
        self.main_window = main_window  # Referência direta ao MainWindow
        self.vispy_widget = vispy_widget
        self.colors = vispy_widget.biome_configs.copy()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Editor de Cores</b>"))

        self.color_list = QWidget()
        self.color_layout = QVBoxLayout()
        self.color_layout.setSpacing(2)
        self.color_list.setLayout(self.color_layout)
        layout.addWidget(self.color_list)

        add_btn = QPushButton("+ Adicionar Cor")
        add_btn.clicked.connect(self.add_color)
        layout.addWidget(add_btn)

        apply_btn = QPushButton("Aplicar e Atualizar Visualização")
        apply_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        apply_btn.clicked.connect(self.apply_to_vispy)
        layout.addWidget(apply_btn)

        layout.addStretch()
        self.setLayout(layout)

        self.refresh_list()

    def get_sorted_colors(self):
        return sorted(self.colors, key=lambda b: b['min'])

    def refresh_list(self):
        # Limpa tudo
        while self.color_layout.count():
            item = self.color_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sorted_colors = self.get_sorted_colors()
        for i, biome in enumerate(sorted_colors):
            row = QHBoxLayout()
            row.setSpacing(5)

            # Preview cor
            color_btn = QToolButton()
            color_btn.setFixedSize(30, 30)
            pixmap = QPixmap(30, 30)
            pixmap.fill(QColor.fromRgbF(*biome['color']))
            color_btn.setIcon(QIcon(pixmap))
            color_btn.setIconSize(QSize(30, 30))
            color_btn.clicked.connect(lambda _, idx=i: self.edit_color(idx))
            row.addWidget(color_btn)

            # Spins min/max
            min_spin = QDoubleSpinBox()
            min_spin.setRange(0.0, 10.0)
            min_spin.setDecimals(3)
            min_spin.setSingleStep(0.01)
            min_spin.setValue(biome['min'])
            min_spin.valueChanged.connect(lambda v, idx=i: self.update_min(idx, v))

            max_spin = QDoubleSpinBox()
            max_spin.setRange(0.0, 10.0)
            max_spin.setDecimals(3)
            max_spin.setSingleStep(0.01)
            max_spin.setValue(biome['max'])
            max_spin.valueChanged.connect(lambda v, idx=i: self.update_max(idx, v))

            row.addWidget(QLabel("De:"))
            row.addWidget(min_spin)
            row.addWidget(QLabel("Até:"))
            row.addWidget(max_spin)

            # Remover
            rem_btn = QToolButton()
            rem_btn.setText("✖")
            rem_btn.clicked.connect(lambda _, idx=i: self.remove_biome(idx))
            row.addWidget(rem_btn)

            row.addStretch()

            # Container simples sem stylesheet problemático
            container = QWidget()
            container.setLayout(row)
            container.setStyleSheet("""
                QWidget {
                    border: 1px solid gray;
                    border-radius: 2px;
                    padding: 4px;
                    background-color: #2f2f2f;
                }
            """)
            self.color_layout.addWidget(container)

    def add_color(self):
        sorted_colors = self.get_sorted_colors()
        new_min = sorted_colors[-1]['max'] if sorted_colors else 0.0
        new_max = max(new_min + 0.1, 1.5)
        new_color = [1.0, 1.0, 1.0, 1.0]
        self.colors.append({'min': new_min, 'max': new_max, 'color': new_color})
        self.refresh_list()

    def remove_biome(self, index):
        sorted_colors = self.get_sorted_colors()
        biome_to_remove = sorted_colors[index]
        self.colors.remove(biome_to_remove)
        self.refresh_list()

    def edit_color(self, index):
        sorted_colors = self.get_sorted_colors()
        biome = sorted_colors[index]
        qcolor = QColor.fromRgbF(*biome['color'])
        dialog = QColorDialog(qcolor, self)
        if dialog.exec():
            new_color = dialog.currentColor()
            biome['color'] = [new_color.redF(), new_color.greenF(), new_color.blueF(), new_color.alphaF()]
            self.refresh_list()

    def update_min(self, index, value):
        sorted_colors = self.get_sorted_colors()
        biome = sorted_colors[index]
        if index > 0 and value < sorted_colors[index-1]['max']:
            value = sorted_colors[index-1]['max']
        biome['min'] = value
        self.refresh_list()

    def update_max(self, index, value):
        sorted_colors = self.get_sorted_colors()
        biome = sorted_colors[index]
        if index + 1 < len(sorted_colors) and value > sorted_colors[index+1]['min']:
            value = sorted_colors[index+1]['min']
        biome['max'] = value
        self.refresh_list()

    def apply_to_vispy(self):
        self.vispy_widget.biome_configs = self.get_sorted_colors()
        self.vispy_widget.update_visualization(self.main_window.pending_amplitude)  # Acesso direto!


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terrain Studio - Perlin Noise 3D")
        self.setGeometry(100, 100, 1400, 900)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Arquivo")
        #edit_menu = menu_bar.addMenu("Editar")
        #tools_menu = menu_bar.addMenu("Ferramentas")

        # Central
        tab_widget = QTabWidget()
        vispy_container = QWidget()
        vispy_layout = QVBoxLayout()

        self.model = TerrainModel()
        self.vispy_widget = VisPyCanvas(self.model)
        vispy_layout.addWidget(self.vispy_widget.native)

        self.pending_amplitude = 150.0
        self.label_altura = QLabel("Amplitude Visual (Z-Scale): 150.0")
        vispy_layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(150)
        self.slider.setValue(150)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        vispy_layout.addWidget(self.slider)

        self.exporter = HeightmapExporter()
        export_btn = QPushButton("Exportar Heightmap (PNG 16-bit)")
        export_btn.clicked.connect(self.export_terrain)
        vispy_layout.addWidget(export_btn)

        vispy_container.setLayout(vispy_layout)
        tab_widget.addTab(vispy_container, "Mapa Principal")
        self.setCentralWidget(tab_widget)

        # Dock com abas internas
        self.config_dock = QDockWidget("Configurações", self)
        self.config_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                     QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                     QDockWidget.DockWidgetFeature.DockWidgetClosable)

        config_tabs = QTabWidget()

        self.setup_form = SetupForm(on_generate_callback=self.on_generate_request)
        config_tabs.addTab(self.setup_form, "Geração")

        # Passa self (MainWindow) e o vispy_widget
        self.biome_editor = ColorEditorWidget(self, self.vispy_widget)
        config_tabs.addTab(self.biome_editor, "Cores")

        self.config_dock.setWidget(config_tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.config_dock)
        self.config_dock.setMinimumWidth(380)

        self.setup_form.collect_and_emit()

    def on_generate_request(self, params):
        old_shape = self.model.shape
        self.model.configure_and_generate(params)

        new_shape = self.model.shape
        if old_shape != new_shape:
            self.vispy_widget.faces = self.model.get_mesh_faces()
            self.vispy_widget.update_camera()

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