from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.ui.styles import SKILL_ICONS

class PlaceholderWidget(QWidget):
    def __init__(self, page_name):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = SKILL_ICONS.get(page_name, 'o')
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet('font-size:48px;')
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(page_name)
        name_lbl.setStyleSheet('font-size:24px;font-weight:bold;color:#F1F5F9;margin-top:16px;')
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        soon_lbl = QLabel('Tez kunda...')
        soon_lbl.setStyleSheet('font-size:14px;color:#475569;')
        soon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl)
        layout.addWidget(soon_lbl)
