from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel,
    QPushButton, QWidget,
    QColorDialog, QHBoxLayout, QToolButton,
    QDoubleSpinBox
)
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize


class ColorEditorWidget(QWidget):
    def __init__(self, main_window, vispy_widget):
        super().__init__()
        self.main_window = main_window  # Referência direta ao MainWindow !!!!!!!! (Facilita acesso das configs aninhadas...)
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
            color_btn.setFixedSize(20, 20)
            pixmap = QPixmap(20, 20)
            pixmap.fill(QColor.fromRgbF(*biome['color']))
            color_btn.setIcon(QIcon(pixmap))
            color_btn.setIconSize(QSize(20, 20))
            color_btn.clicked.connect(lambda _, idx=i: self.edit_color(idx))
            row.addWidget(color_btn)

            # Spins min/max
            min_spin = QDoubleSpinBox()
            min_spin.setRange(0.0, 10.0)
            min_spin.setDecimals(3)
            min_spin.setSingleStep(0.01)
            min_spin.setValue(biome['min'])
            min_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            min_spin.valueChanged.connect(lambda v, idx=i: self.update_min(idx, v))
            
            

            max_spin = QDoubleSpinBox()
            max_spin.setRange(0.0, 10.0)
            max_spin.setDecimals(3)
            max_spin.setSingleStep(0.01)
            max_spin.setValue(biome['max'])
            max_spin.valueChanged.connect(lambda v, idx=i: self.update_max(idx, v))

            row.addWidget(min_spin)
            row.addWidget(QLabel("To:"))
            row.addWidget(max_spin)

            # Remover
            rem_btn = QToolButton()
            rem_btn.setIcon(QIcon.fromTheme("edit-delete"))
            rem_btn.clicked.connect(lambda _, idx=i: self.remove_biome(idx))
            row.addWidget(rem_btn)

            row.addStretch()

            container = QWidget()
            container.setLayout(row)
            container.setStyleSheet("""
                QWidget {
                    border: 1px solid gray;
                    border-radius: 2px;
                    background-color: #2f2f2f;
                }
            """)
            self.color_layout.addWidget(container)

    def add_color(self):
        new_min =  0.0
        new_max = 0.0
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
        self.vispy_widget.update_visualization(self.main_window.pending_amplitude)  # Acesso direto!!!!
