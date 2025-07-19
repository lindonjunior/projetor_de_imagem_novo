# core/canvas_state.py

from PySide6.QtCore import QObject, Signal, QRectF, QPointF
from PySide6.QtGui import QColor, QPainterPath

class DrawingStroke:
    def __init__(self, path: QPainterPath, color: QColor, thickness: float):
        self.path = path
        self.color = color
        self.thickness = thickness

class CanvasState(QObject):
    state_changed = Signal()
    laser_position_changed = Signal()

    def __init__(self):
        super().__init__()
        self.rotation = 0
        self.brightness = 1.0
        self.contrast_applied = False
        self.display_mode = "Ajustar (Fit)"
        self.zoom_enabled = False
        self.zoom_rect = QRectF(0.25, 0.25, 0.5, 0.5) 
        self.active_tool = "none"
        self.pen_color = QColor("#ff0000")
        self.pen_thickness = 5.0
        self.highlighter_color = QColor(255, 255, 0, 100)
        self.highlighter_thickness = 25.0
        self.strokes = []
        self.laser_position = None
        self.laser_style = "Brilho Intenso"
        self.laser_animation_frame = 0
        self.projection_aspect_ratio = 16.0 / 9.0
        
        # --- NOVO: Estado para a rotação da lupa ---
        self.lupa_rotation = 0 # Pode ser 0, 90, 180, 270

    def add_stroke(self, path: QPainterPath):
        if self.active_tool == "pen":
            stroke = DrawingStroke(path, self.pen_color, self.pen_thickness)
            self.strokes.append(stroke)
            self.state_changed.emit()
        elif self.active_tool == "highlighter":
            stroke = DrawingStroke(path, self.highlighter_color, self.highlighter_thickness)
            self.strokes.append(stroke)
            self.state_changed.emit()

    def clear_drawings(self):
        if self.strokes:
            self.strokes.clear()
            self.state_changed.emit()

    def update_laser_position(self, pos: QPointF | None):
        if self.laser_position != pos:
            self.laser_position = pos
            self.laser_position_changed.emit()

    def set_property(self, name, value):
        if hasattr(self, name) and getattr(self, name) != value:
            setattr(self, name, value)
            if name == 'laser_style':
                self.laser_position_changed.emit()
            else:
                self.state_changed.emit()

