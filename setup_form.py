import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, 
    QCheckBox, QGroupBox, QPushButton, QFileDialog, QMessageBox
)

class SetupForm(QWidget):
    def __init__(self, on_generate_callback):
        super().__init__()
        self.on_generate_callback = on_generate_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # --- Grupo: Configurações Gerais ---
        grp_gen = QGroupBox("Geral")
        form_gen = QFormLayout()
        
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999)
        self.spin_seed.setValue(242)
        form_gen.addRow("Global Seed:", self.spin_seed)
        
        self.spin_size = QSpinBox()
        self.spin_size.setRange(50, 2000)
        self.spin_size.setSingleStep(50)
        self.spin_size.setValue(500) 
        form_gen.addRow("Map Size (px):", self.spin_size)
        
        self.spin_octaves = QSpinBox()
        self.spin_octaves.setRange(2, 16)
        self.spin_octaves.setValue(6)
        form_gen.addRow("Octaves (Detalhe):", self.spin_octaves)
        
        grp_gen.setLayout(form_gen)
        layout.addWidget(grp_gen)
        
        # --- Grupo: Base Height Map ---
        self.grp_base = QGroupBox("Base Height Map")
        self.grp_base.setCheckable(True)
        self.grp_base.setChecked(True)
        form_base = QFormLayout()
        
        self.spin_base_scale = QDoubleSpinBox()
        self.spin_base_scale.setRange(0.001, 0.01)
        self.spin_base_scale.setDecimals(4)
        self.spin_base_scale.setSingleStep(0.0005)
        self.spin_base_scale.setValue(0.005)
        form_base.addRow("Base Scale:", self.spin_base_scale)
        
        self.spin_seed_adder = QSpinBox()
        self.spin_seed_adder.setRange(1, 1000)
        self.spin_seed_adder.setValue(100)
        form_base.addRow("Seed Adder:", self.spin_seed_adder)
        
        self.spin_amplitude_factor = QDoubleSpinBox()
        self.spin_amplitude_factor.setRange(0.1, 1.0)
        self.spin_amplitude_factor.setSingleStep(0.1)
        self.spin_amplitude_factor.setValue(0.7)
        form_base.addRow("Detalhe Amp. Factor:", self.spin_amplitude_factor)
        
        self.spin_clip = QDoubleSpinBox()
        self.spin_clip.setRange(1.0, 1.5)
        self.spin_clip.setSingleStep(0.1)
        self.spin_clip.setValue(1.5)
        form_base.addRow("Clip Max Height:", self.spin_clip)
        
        self.spin_base_octaves = QSpinBox()
        self.spin_base_octaves.setRange(2, 8)
        self.spin_base_octaves.setValue(4)
        form_base.addRow("Base Octaves:", self.spin_base_octaves)
        
        self.grp_base.setLayout(form_base)
        layout.addWidget(self.grp_base)
        
        # --- Botões de Ação ---
        btn_layout = QVBoxLayout()
        
        self.btn_generate = QPushButton("GERAR MAPA")
        self.btn_generate.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;")
        self.btn_generate.clicked.connect(self.collect_and_emit)
        btn_layout.addWidget(self.btn_generate)
        
        self.btn_save_json = QPushButton("Salvar Preset (JSON)")
        self.btn_save_json.clicked.connect(self.save_to_json)
        btn_layout.addWidget(self.btn_save_json)
        
        self.btn_load_json = QPushButton("Carregar Preset (JSON)")
        self.btn_load_json.clicked.connect(self.load_from_json)
        btn_layout.addWidget(self.btn_load_json)
        
        layout.addLayout(btn_layout)
        layout.addStretch() # Empurra tudo pra cima
        
        self.setLayout(layout)

    def collect_data(self):
        """Coleta todos os dados do formulário em um dicionário."""
        data = {
            "seed": self.spin_seed.value(),
            "map_size": self.spin_size.value(),
            "octaves": self.spin_octaves.value(),
            "use_base_map": self.grp_base.isChecked(),
            
            # Só importa se use_base_map for True
            "base_scale": self.spin_base_scale.value(),
            "seed_adder": self.spin_seed_adder.value(),
            "amplitude_factor": self.spin_amplitude_factor.value(),
            "clip_max": self.spin_clip.value(),
            "octaves_base": self.spin_base_octaves.value()
        }
        return data

    def collect_and_emit(self):
        data = self.collect_data()
        self.on_generate_callback(data)

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Preset", "meu_setup.json", "JSON Files (*.json)")
        if file_path:
            data = self.collect_data()
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                QMessageBox.information(self, "Sucesso", "Preset salvo com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Carregar Preset", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.apply_data(data)
                QMessageBox.information(self, "Sucesso", "Preset carregado! Clique em Gerar Mapa.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar: {str(e)}")

    def apply_data(self, data):
        """Preenche o formulário com dados carregados."""
        self.spin_seed.setValue(data.get("seed", 242))
        self.spin_size.setValue(data.get("map_size", 200))
        self.spin_octaves.setValue(data.get("octaves", 6))
        self.grp_base.setChecked(data.get("use_base_map", True))
        
        self.spin_base_scale.setValue(data.get("base_scale", 0.005))
        self.spin_seed_adder.setValue(data.get("seed_adder", 100))
        self.spin_amplitude_factor.setValue(data.get("amplitude_factor", 0.2))
        self.spin_clip.setValue(data.get("clip_max", 1.5))
        self.spin_base_octaves.setValue(data.get("octaves_base", 4))