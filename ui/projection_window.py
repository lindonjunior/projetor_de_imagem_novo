# ui/projection_window.py

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPen
from PySide6.QtCore import Qt, QTimer, Slot

logger = logging.getLogger("ImageProjectorLogger")

class ProjectionWindow(QWidget):
    DISPLAY_MODES = {
        "Ajustar (Fit)": Qt.AspectRatioMode.KeepAspectRatio,
        "Preencher (Fill)": Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        "Esticar (Stretch)": Qt.AspectRatioMode.IgnoreAspectRatio,
        "Centralizar (Center)": None,
        "Lado a Lado (Tile)": None,
    }

    def __init__(self, screen):
        super().__init__()
        self.setWindowTitle("Projeção")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(screen.geometry())
        
        self.base_pixmap = None
        self.canvas_state = None
        self.background_color = QColor("#000000")
        self.setStyleSheet(f"background-color: {self.background_color.name()};")
        
        # Timer para animação do laser
        self.laser_timer = QTimer(self)
        self.laser_timer.timeout.connect(self.animate_laser)
        self.laser_timer.start(30) # ~33 FPS

        logger.info(f"Janela de projeção criada para a tela {screen.name()}.")

    def update_display(self, pixmap: QPixmap, state):
        """Recebe a imagem final (com desenhos e zoom já aplicados) e a exibe."""
        self.base_pixmap = pixmap
        self.canvas_state = state
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.base_pixmap or not self.canvas_state:
            painter.fillRect(self.rect(), self.background_color)
            return

        painter.fillRect(self.rect(), self.background_color)
        
        display_mode_name = self.canvas_state.display_mode
        mode = self.DISPLAY_MODES.get(display_mode_name)
        
        if display_mode_name == "Lado a Lado (Tile)":
            painter.fillRect(self.rect(), QBrush(self.base_pixmap))
        elif display_mode_name == "Centralizar (Center)":
            scaled_pixmap = self.base_pixmap
            image_draw_rect = scaled_pixmap.rect()
            image_draw_rect.moveCenter(self.rect().center())
            painter.drawPixmap(image_draw_rect.topLeft(), scaled_pixmap)
        else:
            scaled_pixmap = self.base_pixmap.scaled(self.size(), mode, Qt.TransformationMode.SmoothTransformation)
            image_draw_rect = scaled_pixmap.rect()
            image_draw_rect.moveCenter(self.rect().center())
            painter.drawPixmap(image_draw_rect.topLeft(), scaled_pixmap)

        # Desenha o laser se estiver ativo
        if self.canvas_state.active_tool == 'laser' and self.canvas_state.laser_position:
            self.draw_laser_pointer(painter)

    def draw_laser_pointer(self, painter: QPainter):
        state = self.canvas_state
        if not state or not state.laser_position:
            return

        # Converte a posição relativa (0-1) para a coordenada da janela
        pos_x = self.rect().x() + state.laser_position.x() * self.rect().width()
        pos_y = self.rect().y() + state.laser_position.y() * self.rect().height()
        
        frame = state.laser_animation_frame
        
        if state.laser_style == "Brilho Intenso":
            outer_radius = 15 + 5 * (1 + (frame % 10) / 10) # Pulsante
            inner_radius = 5
            
            # Outer glow
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0, 50))
            painter.drawEllipse(QPointF(pos_x, pos_y), outer_radius, outer_radius)
            
            # Inner circle
            painter.setBrush(QColor(255, 100, 100, 255))
            painter.drawEllipse(QPointF(pos_x, pos_y), inner_radius, inner_radius)

    @Slot()
    def animate_laser(self):
        if self.canvas_state:
            self.canvas_state.laser_animation_frame += 1
            if self.canvas_state.active_tool == 'laser':
                self.update() # Redesenha a janela para animar o laser

    def set_background_color(self, color_hex: str):
        self.background_color = QColor(color_hex)
        self.update() # Força o redesenho com a nova cor

    def keyPressEvent(self, event):
        # Este evento é encaminhado da MainWindow, então não precisamos fechar aqui
        super().keyPressEvent(event)

