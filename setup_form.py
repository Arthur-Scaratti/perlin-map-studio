import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox,
    QGroupBox, QPushButton, QFileDialog, QMessageBox,
    QHBoxLayout, QButtonGroup, QRadioButton
)


class SetupForm(QWidget):
    def __init__(self, on_generate_callback):
        super().__init__()
        self.on_generate_callback = on_generate_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        grp_gen = QGroupBox("General Settings")
        form_gen = QFormLayout()
        
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 999999)
        self.spin_seed.setValue(13)
        form_gen.addRow("Global Seed:", self.spin_seed)

        self.spin_continents = QSpinBox()
        self.spin_continents.setRange(1, 5)
        self.spin_continents.setValue(5)
        form_gen.addRow("Qty. Continents:", self.spin_continents)

        self.spin_cont_size = QDoubleSpinBox()
        self.spin_cont_size.setRange(0.02, 0.30)
        self.spin_cont_size.setSingleStep(0.01)
        self.spin_cont_size.setValue(0.06)
        self.spin_cont_size.setToolTip("Aumente para continentes maiores ou diminua para ilhas isoladas.")
        form_gen.addRow("Tamanho Continentes:", self.spin_cont_size)
        
        grp_gen.setLayout(form_gen)
        layout.addWidget(grp_gen)

        # =========================
        # Shape Selection
        # =========================
        grp_shape = QGroupBox("Shape")
        shape_layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        self.shape_group = QButtonGroup(self)
        self.shape_group.setExclusive(True)

        self.rb_square = QRadioButton("Square")
        self.rb_round = QRadioButton("Round")
        self.rb_sphere = QRadioButton("Equirectangular")

        self.rb_round.setChecked(True)

        self.shape_group.addButton(self.rb_square)
        self.shape_group.addButton(self.rb_round)
        self.shape_group.addButton(self.rb_sphere)

        btn_row.addWidget(self.rb_square)
        btn_row.addWidget(self.rb_round)
        btn_row.addWidget(self.rb_sphere)

        shape_layout.addLayout(btn_row)

        #################################
        self.grp_square = QGroupBox("Square Config")
        form_square = QFormLayout()

        self.spin_square_side = QSpinBox()
        self.spin_square_side.setRange(50, 10000)
        self.spin_square_side.setValue(513)
        form_square.addRow("Side:", self.spin_square_side)

        self.grp_square.setLayout(form_square)
        shape_layout.addWidget(self.grp_square)

        ################################
        self.grp_round = QGroupBox("Round Config")
        form_round = QFormLayout()

        self.spin_round_radius = QSpinBox()
        self.spin_round_radius.setRange(50, 10000)
        self.spin_round_radius.setValue(513)
        form_round.addRow("Radius:", self.spin_round_radius)

        self.grp_round.setLayout(form_round)
        self.grp_round.setVisible(False)
        shape_layout.addWidget(self.grp_round)

        ################################
        self.grp_sphere = QGroupBox("Sphere Config")
        form_sphere = QFormLayout()

        self.spin_sphere_height = QSpinBox()
        self.spin_sphere_height.setRange(50, 10000)
        self.spin_sphere_height.setSingleStep(10)
        self.spin_sphere_height.setValue(513)
        form_sphere.addRow("Height:", self.spin_sphere_height)

        self.grp_sphere.setLayout(form_sphere)
        self.grp_sphere.setVisible(False)
        shape_layout.addWidget(self.grp_sphere)

        ################################ toggle
        self.rb_square.toggled.connect(self.update_shape_visibility)
        self.rb_round.toggled.connect(self.update_shape_visibility)
        self.rb_sphere.toggled.connect(self.update_shape_visibility)

        grp_shape.setLayout(shape_layout)
        layout.addWidget(grp_shape)
        ################################
        
        ################################
        self.grp_base = QGroupBox("Base Height Map")
        self.grp_base.setCheckable(True)
        self.grp_base.setChecked(True)
        form_base = QFormLayout()
         
        self.spin_seed_adder = QSpinBox()
        self.spin_seed_adder.setRange(0, 1000)
        self.spin_seed_adder.setValue(0)
        form_base.addRow("Base Seed Inc. :", self.spin_seed_adder)

        self.spin_base_scale = QDoubleSpinBox()
        self.spin_base_scale.setRange(0.0001, 0.01)
        self.spin_base_scale.setDecimals(4)
        self.spin_base_scale.setSingleStep(0.0005)
        self.spin_base_scale.setValue(0.0045)
        form_base.addRow("Base Scale:", self.spin_base_scale)

        self.spin_base_octaves = QSpinBox()
        self.spin_base_octaves.setRange(1, 8)
        self.spin_base_octaves.setValue(4)
        form_base.addRow("Base Octaves:", self.spin_base_octaves)

        self.spin_base_persistence = QDoubleSpinBox()
        self.spin_base_persistence.setRange(0.1, 1.0)
        self.spin_base_persistence.setSingleStep(0.01)
        self.spin_base_persistence.setValue(0.6)
        form_base.addRow("Base Persistence:", self.spin_base_persistence)

        self.spin_base_lacunarity = QDoubleSpinBox()
        self.spin_base_lacunarity.setRange(1.0, 3.0)
        self.spin_base_lacunarity.setSingleStep(0.05)
        self.spin_base_lacunarity.setValue(2.0)
        form_base.addRow("Base Lacunarity:", self.spin_base_lacunarity)
        
        self.grp_base.setLayout(form_base)
        layout.addWidget(self.grp_base)
        
        # =========================
        # Upper Height Map
        # =========================

        self.grp_upper = QGroupBox("Upper Height Map")
        form_upper = QFormLayout()
        
        self.spin_amplitude_factor = QDoubleSpinBox()
        self.spin_amplitude_factor.setRange(0.1, 1.0)
        self.spin_amplitude_factor.setSingleStep(0.1)
        self.spin_amplitude_factor.setValue(1.0)
        form_upper.addRow("Upper Amp. Factor:", self.spin_amplitude_factor)
        
        self.spin_clip = QDoubleSpinBox()
        self.spin_clip.setRange(1.0, 1.5)
        self.spin_clip.setSingleStep(0.1)
        self.spin_clip.setValue(1.5)
        form_upper.addRow("Clip Max Height:", self.spin_clip)
        
        self.spin_upper_scale = QDoubleSpinBox()
        self.spin_upper_scale.setRange(0.0001, 0.1)
        self.spin_upper_scale.setDecimals(4)
        self.spin_upper_scale.setSingleStep(0.0005)
        self.spin_upper_scale.setValue(0.011)
        form_upper.addRow("Upper Scale:", self.spin_upper_scale)

        self.spin_octaves = QSpinBox()
        self.spin_octaves.setRange(2, 16)
        self.spin_octaves.setValue(8)
        form_upper.addRow("Upper Octaves:", self.spin_octaves)

        self.spin_persistence = QDoubleSpinBox()
        self.spin_persistence.setRange(0.1, 1.0)
        self.spin_persistence.setSingleStep(0.01)
        self.spin_persistence.setValue(0.5)
        form_upper.addRow("Upper Persistence:", self.spin_persistence)

        self.spin_lacunarity = QDoubleSpinBox()
        self.spin_lacunarity.setRange(1.0, 3.0)
        self.spin_lacunarity.setSingleStep(0.05)
        self.spin_lacunarity.setValue(2.1)
        form_upper.addRow("Upper Lacunarity:", self.spin_lacunarity)

        self.grp_upper.setLayout(form_upper)
        layout.addWidget(self.grp_upper)

        # =========================
        # Buttons
        # =========================
        
        btn_layout = QVBoxLayout()
        
        self.btn_generate = QPushButton("Build")
        self.btn_generate.setStyleSheet("font-size: 14px; padding: 10px; background-color: #4CAF50; color: white;")
        self.btn_generate.clicked.connect(self.collect_and_emit)
        btn_layout.addWidget(self.btn_generate)
        
        self.btn_save_json = QPushButton("Save Preset (JSON)")
        self.btn_save_json.clicked.connect(self.save_to_json)
        btn_layout.addWidget(self.btn_save_json)
        
        self.btn_load_json = QPushButton("Load Preset (JSON)")
        self.btn_load_json.clicked.connect(self.load_from_json)
        btn_layout.addWidget(self.btn_load_json)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)


    def update_shape_visibility(self):
        self.grp_square.setVisible(self.rb_square.isChecked())
        self.grp_round.setVisible(self.rb_round.isChecked())
        self.grp_sphere.setVisible(self.rb_sphere.isChecked())

    def collect_data(self):
        if self.rb_square.isChecked():
            shape = "square"
            shape_params = {
                "side": self.spin_square_side.value()
            }
        elif self.rb_round.isChecked():
            shape = "round"
            shape_params = {
                "radius": self.spin_round_radius.value()
            }
        else:
            shape = "sphere"
            shape_params = {
                "height": self.spin_sphere_height.value()
            }
    
        data = {
            "seed": self.spin_seed.value(),
            "continents_count": self.spin_continents.value(),
            "continent_size": self.spin_cont_size.value(),
            "octaves": self.spin_octaves.value(),

            "shape": shape,
            "shape_params": shape_params,

            "use_base_map": self.grp_base.isChecked(),
            "base_scale": self.spin_base_scale.value(),
            "upper_scale": self.spin_upper_scale.value(),
            "seed_adder": self.spin_seed_adder.value(),
            "amplitude_factor": self.spin_amplitude_factor.value(),
            "clip_max": self.spin_clip.value(),
            "octaves_base": self.spin_base_octaves.value(),
            "persistence": self.spin_persistence.value(),
            "lacunarity": self.spin_lacunarity.value(),
            "base_persistence": self.spin_base_persistence.value(),
            "base_lacunarity": self.spin_base_lacunarity.value()
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
        self.spin_seed.setValue(data.get("seed", 242))
        self.spin_continents.setValue(data.get("continents_count", 1)),
        self.spin_cont_size.setValue(data.get("continent_size", 0.25))
        self.spin_octaves.setValue(data.get("octaves", 6))
        self.grp_base.setChecked(data.get("use_base_map", True))
        
        self.spin_base_scale.setValue(data.get("base_scale", 0.005))
        ####
        self.spin_persistence.setValue(data.get("persistence", 0.5))
        self.spin_lacunarity.setValue(data.get("lacunarity", 2.0))

        self.spin_base_persistence.setValue(data.get("base_persistence", 0.5))
        self.spin_base_lacunarity.setValue(data.get("base_lacunarity", 2))
        ####
        self.spin_upper_scale.setValue(data.get("upper_scale", 0.01))
        self.spin_seed_adder.setValue(data.get("seed_adder", 100))
        self.spin_amplitude_factor.setValue(data.get("amplitude_factor", 0.7))
        self.spin_clip.setValue(data.get("clip_max", 1.5))
        self.spin_base_octaves.setValue(data.get("octaves_base", 4))