from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QWidget,
    QColorDialog, QHBoxLayout, QToolButton,
    QDoubleSpinBox, QGroupBox, QFormLayout, QScrollArea
)
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtCore import Qt

class ColorEditorWidget(QWidget):
    def __init__(self, main_window, vispy_widget):
        super().__init__()
        self.main_window = main_window
        self.vispy_widget = vispy_widget
        
        self.colors = []
        if hasattr(self.vispy_widget, 'biome_configs'):
            for item in self.vispy_widget.biome_configs:
                # Mantém compatibilidade com o formato antigo (min) e o novo (start)
                val = item.get('start', item.get('min', 0.0))
                self.colors.append({'start': val, 'color': item['color']})
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.color_layout = QVBoxLayout(self.scroll_content)
        self.color_layout.setSpacing(10)
        self.color_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

        # Botões Inferiores
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("+ Adicionar Novo Range")
        add_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #333; color: white;")
        add_btn.clicked.connect(self.add_range)
        btn_layout.addWidget(add_btn)

        self.apply_btn = QPushButton("ATUALIZAR VISUALIZAÇÃO")
        self.apply_btn.setStyleSheet("""
            font-weight: bold; padding: 12px; 
            background-color: #4CAF50; color: white; border-radius: 4px;
        """)
        self.apply_btn.clicked.connect(self.apply_to_vispy)
        btn_layout.addWidget(self.apply_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.refresh_list()

    def get_sorted_colors(self):
        return sorted(self.colors, key=lambda x: x['start'])

    def refresh_list(self):
        # Limpa o layout com segurança
        while self.color_layout.count():
            item = self.color_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Sempre trabalhamos com a lista ordenada por altura na UI
        self.colors = self.get_sorted_colors()
        
        for i, data in enumerate(self.colors):
            group = QGroupBox()
            group_layout = QVBoxLayout(group)
            
            title_row = QHBoxLayout()
            title_label = QLabel(f"<b># {i+1}</b>")
            
           # Botão Remover
            rem_btn = QPushButton("Remover")
            rem_btn.setStyleSheet("color: red; border: none; font-size: 10px; text-align: right;")
            rem_btn.clicked.connect(lambda _, idx=i: self.remove_range(idx))
            
            
            title_row.addWidget(title_label)
            title_row.addStretch()
            title_row.addWidget(rem_btn)
            
            group_layout.addLayout(title_row)

            # --- Formulário de Dados ---
            form = QFormLayout()
            
            # Cor
            color_row = QHBoxLayout()
            color_btn = QToolButton()
            color_btn.setFixedSize(32, 22)
            pixmap = QPixmap(30, 15)
            pixmap.fill(QColor.fromRgbF(*data['color']))
            color_btn.setIcon(QIcon(pixmap))
            color_btn.clicked.connect(lambda _, idx=i: self.edit_color(idx))
            
            color_hex = QColor.fromRgbF(*data['color']).name().upper()
            color_row.addWidget(color_btn)
            color_row.addWidget(QLabel(color_hex))
            form.addRow("Aparência:", color_row)

            # Entrada (Start)
            start_spin = QDoubleSpinBox()
            start_spin.setRange(0, 1.5) 
            start_spin.setDecimals(3)
            start_spin.setSingleStep(0.01)
            start_spin.setValue(data['start'])
            start_spin.valueChanged.connect(lambda v, idx=i: self.update_val(idx, v))
            
            limit = f"até {self.colors[i+1]['start']:.2f}" if i+1 < len(self.colors) else "em diante"
            form.addRow(f"Início ({limit}):", start_spin)

            group_layout.addLayout(form)

            

            self.color_layout.addWidget(group)

    def move_layer(self, index, delta):
       
        target = index + delta
        # Troca apenas a informação de cor, mantém o 'start' do slot
        self.colors[index]['color'], self.colors[target]['color'] = \
            self.colors[target]['color'], self.colors[index]['color']
        self.refresh_list()

    def update_val(self, index, val):
        self.colors[index]['start'] = val

    def add_range(self):
        last_val = self.colors[-1]['start'] if self.colors else 0.0
        self.colors.append({'start': last_val + 0.1, 'color': [0.5, 0.5, 0.5, 1.0]})
        self.refresh_list()

    def remove_range(self, index):
        if len(self.colors) > 1:
            self.colors.pop(index)
            self.refresh_list()

    def edit_color(self, index):
        dialog = QColorDialog(QColor.fromRgbF(*self.colors[index]['color']), self)
        if dialog.exec():
            c = dialog.currentColor()
            self.colors[index]['color'] = [c.redF(), c.greenF(), c.blueF(), c.alphaF()]
            self.refresh_list()

    def apply_to_vispy(self):
        self.colors = self.get_sorted_colors() # Garante ordem antes de aplicar
        
        final_configs = []

        try:
            abs_max = self.main_window.setup_form.spin_clip.value()
        except:
            abs_max = 10.0

        for i in range(len(self.colors)):
            c_start = self.colors[i]['start']
            c_next = self.colors[i+1]['start'] if i+1 < len(self.colors) else abs_max
            
            final_configs.append({
                'min': c_start,
                'max': c_next,
                'color': self.colors[i]['color'],
                'start': c_start # Para persistência
            })
            
        self.vispy_widget.biome_configs = final_configs
        self.vispy_widget.update_visualization(self.main_window.pending_amplitude)
        self.refresh_list()