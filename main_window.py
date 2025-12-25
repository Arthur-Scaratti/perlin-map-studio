import time
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QSlider, QLabel, QFileDialog,
    QMessageBox, QPushButton, QDockWidget, QWidget,
    QTabWidget
)
from PyQt6.QtGui import QAction, QKeySequence
from project_manager import ProjectManager
from PyQt6.QtCore import Qt

from exporter import HeightmapExporter
from terrain_model import TerrainModel
from vispy_canvas import VisPyCanvas
from setup_form import SetupForm
from color_setup import ColorEditorWidget

import os
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SAVED_MAPS_DIR = os.path.join(PROJECT_ROOT, "saved_maps")
EXPORTED_HEIGHTMAPS_DIR = os.path.join(PROJECT_ROOT, "exported_heightmaps")
PRESETS_DIR = os.path.join(PROJECT_ROOT, "presets")

os.makedirs(SAVED_MAPS_DIR, exist_ok=True)
os.makedirs(EXPORTED_HEIGHTMAPS_DIR, exist_ok=True)
os.makedirs(PRESETS_DIR, exist_ok=True)




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Perlin Map Studio")
        self.setGeometry(100, 100, 1400, 900)
        
        self.current_project_path = None
        self.last_params = {} # Armazena os últimos parâmetros de geração

        # --- Setup do Modelo e UI ---
        self.model = TerrainModel()
        self.setup_ui()
        
        # --- Lógica de Auto-load ---
        last_path = ProjectManager.get_last_project_path()
        if last_path:
            self.load_project_file(last_path)
        else:
            self.setup_form.collect_and_emit()

    def setup_ui(self):
        # Menu Arquivo
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Arquivo")

        new_action = QAction("Novo Projeto", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project_action)
        file_menu.addAction(new_action)

        load_action = QAction("Abrir Projeto...", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self.load_project_action)
        file_menu.addAction(load_action)

        save_action = QAction("Salvar Projeto", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project_action)
        file_menu.addAction(save_action)

        save_as_action = QAction("Salvar Como...", self)
        save_as_action.triggered.connect(lambda: self.save_project_action(force_dialog=True))
        file_menu.addAction(save_as_action)

        # Central Widget com Tabs
        tab_widget = QTabWidget()
        vispy_container = QWidget()
        vispy_layout = QVBoxLayout()

        self.vispy_widget = VisPyCanvas(self.model)
        vispy_layout.addWidget(self.vispy_widget.native)

        self.pending_amplitude = 150.0
        self.label_altura = QLabel("Visual Range (Z-Scale): 150.0")
        vispy_layout.addWidget(self.label_altura)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(250) # Aumentado para mais range
        self.slider.setValue(150)
        self.slider.valueChanged.connect(self.on_amplitude_change)
        vispy_layout.addWidget(self.slider)

        self.exporter = HeightmapExporter()
        export_btn = QPushButton("Export Heightmap (PNG 16-bit)")
        export_btn.clicked.connect(self.export_terrain)
        vispy_layout.addWidget(export_btn)

        vispy_container.setLayout(vispy_layout)
        tab_widget.addTab(vispy_container, "Map View")
        self.setCentralWidget(tab_widget)

        # Docks
        self.config_dock = QDockWidget("Settings", self)
        config_tabs = QTabWidget()
        self.setup_form = SetupForm(on_generate_callback=self.on_generate_request)
        config_tabs.addTab(self.setup_form, "Generation")
        self.biome_editor = ColorEditorWidget(self, self.vispy_widget)
        config_tabs.addTab(self.biome_editor, "Colors")
        self.config_dock.setWidget(config_tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.config_dock)

    # --- LÓGICA DE PROJETO ---

    def new_project_action(self):
        ret = QMessageBox.question(self, "New Project", "Want to start a new project?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            self.current_project_path = None
            self.setup_form.apply_data({}) # Reseta campos
            self.setup_form.collect_and_emit()
            self.setWindowTitle("Terrain Studio - New Project")

    def save_project_action(self, force_dialog=False):
        if not self.current_project_path or force_dialog:
            path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Terrain Project (*.tproj)")
            if not path: return
            self.current_project_path = path

        # Reune os dados necessários para reconstruir o estado
        data = {
            "z_base": self.model.Z_base,
            "mask": self.model.mask,
            "shape": self.model.shape,
            "params": self.last_params,
            "biomes": self.vispy_widget.biome_configs,
            "amplitude": self.pending_amplitude
        }
        
        if ProjectManager.save_project(self.current_project_path, data):
            self.statusBar().showMessage(f"Projeto salvo: {self.current_project_path}", 3000)
            self.setWindowTitle(f"Terrain Studio - {os.path.basename(self.current_project_path)}")

    def load_project_action(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Terrain Project (*.tproj)")
        if path:
            self.load_project_file(path)

    def load_project_file(self, path):
        data = ProjectManager.load_project(path)
        if data:
            self.current_project_path = path
            
           
            self.model.shape = data['shape']
            self.model.Z_base = data['z_base']
            self.model.mask = data['mask']
           
            self.model.X, self.model.Y = np.meshgrid(np.arange(data['shape'][1]), np.arange(data['shape'][0]))
            self.model.X_flat = self.model.X.ravel()
            self.model.Y_flat = self.model.Y.ravel()

            
            self.last_params = data['params']
            self.setup_form.apply_data(data['params'])

            
            self.vispy_widget.biome_configs = data['biomes']
            converted_colors = []
            for b in data['biomes']:
                # Compatibilidade com versões antigas
                start_val = b.get('start', b.get('min', 0.0))
                converted_colors.append({'start': start_val, 'color': b['color']})
        
            self.biome_editor.colors = converted_colors
            self.biome_editor.refresh_list()
           
            self.pending_amplitude = data.get('amplitude', 150.0)
            self.slider.setValue(int(self.pending_amplitude))
            
            
            #self.vispy_widget.faces = self.model.get_mesh_faces()
            self.vispy_widget.update_camera()
            self.vispy_widget.update_visualization(self.pending_amplitude)
            
            self.setWindowTitle(f"Terrain Studio - {os.path.basename(path)}")
            self.statusBar().showMessage(f"Project loaded: {path}", 3000)


    def on_generate_request(self, params):
        start = time.time()
        self.last_params = params
        old_shape = self.model.shape
        self.model.configure_and_generate(params)
        if old_shape != self.model.shape:
            self.vispy_widget.update_camera()
        self.vispy_widget.update_visualization(self.pending_amplitude)
        print(f"[Window] on_generate_request_total: {time.time() - start:.2f}s")

    def on_amplitude_change(self, value):
        self.pending_amplitude = float(value)
        self.label_altura.setText(f"Visual (Z-Scale): {self.pending_amplitude:.1f}")
        self.vispy_widget.update_visualization(self.pending_amplitude)

    def export_terrain(self):
        Z_2D = self.model.Z_base
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Heightmap", "terrain_gen.png", "PNG Files (*.png)")
        if file_path:
            self.exporter.export_heightmap(Z_2D, output_path=file_path)
            QMessageBox.information(self, "Success", f"Saved to:\n{file_path}")