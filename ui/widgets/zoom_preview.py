# ui/widgets/zoom_preview.py

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QTransform

logger = logging.getLogger("ImageProjectorLogger")

class ZoomPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        self.pixmap_to_display = None
        self.canvas_state = None
        self.message_to_show = "Carregue uma pasta ou galeria para começar."
        self.aspect_ratio = 16.0 / 9.0
        
        self.is_dragging_lupa = False
        self.drag_start_pos = QPointF()
        self.rect_start_pos = QPointF()
        
        self.screen_rect = QRectF()
        self.image_on_screen_rect = QRectF()

        self.setMinimumSize(320, 180)

    def set_canvas_state(self, state_object, pixmap):
        self.message_to_show = None
        self.canvas_state = state_object
        self.pixmap_to_display = pixmap
        self.update()

    def show_message(self, message: str):
        self.message_to_show = message
        self.pixmap_to_display = None
        self.canvas_state = None
        self.update()

    def set_aspect_ratio(self, ratio: float):
        if self.aspect_ratio != ratio:
            self.aspect_ratio = ratio
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        widget_rect = self.rect()
        
        target_size = QSize(widget_rect.width(), int(widget_rect.width() / self.aspect_ratio))
        if target_size.height() > widget_rect.height():
            target_size = QSize(int(widget_rect.height() * self.aspect_ratio), widget_rect.height())
        
        self.screen_rect = QRectF(0, 0, target_size.width(), target_size.height())
        self.screen_rect.moveCenter(widget_rect.center())

        painter.eraseRect(widget_rect)
        painter.fillRect(self.screen_rect, Qt.GlobalColor.black)

        if self.message_to_show:
            painter.setPen(Qt.GlobalColor.white)
            flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
            painter.drawText(self.screen_rect, flags, self.message_to_show)
            return

        if not self.pixmap_to_display or not self.canvas_state:
            return

        img_pixmap = self.pixmap_to_display
        scaled_pixmap = img_pixmap.scaled(self.screen_rect.size().toSize(), 
                                          Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
        
        self.image_on_screen_rect = QRectF(scaled_pixmap.rect())
        self.image_on_screen_rect.moveCenter(self.screen_rect.center())
        
        painter.drawPixmap(self.image_on_screen_rect.topLeft(), scaled_pixmap)
        
        self.draw_strokes(painter)
        self.draw_laser_pointer(painter)

        if self.canvas_state.zoom_enabled:
            self.draw_rotated_zoom_rect(painter)

    def draw_rotated_zoom_rect(self, painter: QPainter):
        """Desenha o retângulo de zoom, aplicando a rotação da lupa."""
        state = self.canvas_state
        
        lupa_rect_abs = QRectF(
            self.screen_rect.x() + state.zoom_rect.x() * self.screen_rect.width(),
            self.screen_rect.y() + state.zoom_rect.y() * self.screen_rect.height(),
            state.zoom_rect.width() * self.screen_rect.width(),
            state.zoom_rect.height() * self.screen_rect.height()
        )
        
        painter.save()
        
        transform = QTransform()
        transform.translate(lupa_rect_abs.center().x(), lupa_rect_abs.center().y())
        transform.rotate(state.lupa_rotation)
        transform.translate(-lupa_rect_abs.center().x(), -lupa_rect_abs.center().y())
        painter.setTransform(transform)
        
        pen = QPen(QColor(255, 255, 0, 220), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawRect(lupa_rect_abs)
        
        painter.restore()

    def draw_strokes(self, painter: QPainter):
        state = self.canvas_state
        if not state or not state.strokes:
            return

        painter.save()
        painter.translate(self.image_on_screen_rect.topLeft())
        painter.scale(self.image_on_screen_rect.width(), self.image_on_screen_rect.height())

        for stroke in state.strokes:
            pen = QPen(stroke.color, stroke.thickness, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            pen.setWidthF(stroke.thickness / self.image_on_screen_rect.width())
            painter.setPen(pen)
            painter.drawPath(stroke.path)
        
        painter.restore()

    def draw_laser_pointer(self, painter: QPainter):
        state = self.canvas_state
        if not state or state.active_tool != 'laser' or not state.laser_position:
            return
        
        pos_x = self.screen_rect.x() + state.laser_position.x() * self.screen_rect.width()
        pos_y = self.screen_rect.y() + state.laser_position.y() * self.screen_rect.height()
        
        frame = state.laser_animation_frame
        
        if state.laser_style == "Brilho Intenso":
            outer_radius = 15 + 5 * (1 + (frame % 10) / 10)
            inner_radius = 5
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0, 50))
            painter.drawEllipse(QPointF(pos_x, pos_y), outer_radius, outer_radius)
            
            painter.setBrush(QColor(255, 100, 100, 255))
            painter.drawEllipse(QPointF(pos_x, pos_y), inner_radius, inner_radius)

    def mousePressEvent(self, event):
        if not self.canvas_state or not self.screen_rect.contains(event.position()):
            return

        if self.canvas_state.zoom_enabled:
            state = self.canvas_state
            
            lupa_rect_abs_unrotated = QRectF(
                self.screen_rect.x() + state.zoom_rect.x() * self.screen_rect.width(),
                self.screen_rect.y() + state.zoom_rect.y() * self.screen_rect.height(),
                state.zoom_rect.width() * self.screen_rect.width(),
                state.zoom_rect.height() * self.screen_rect.height()
            )
            
            lupa_center_abs = lupa_rect_abs_unrotated.center()
            inverse_transform = QTransform().translate(lupa_center_abs.x(), lupa_center_abs.y()).rotate(-state.lupa_rotation).translate(-lupa_center_abs.x(), -lupa_center_abs.y())
            
            mouse_pos_unrotated = inverse_transform.map(event.position())

            if lupa_rect_abs_unrotated.contains(mouse_pos_unrotated):
                self.is_dragging_lupa = True
                
                relative_pos_on_screen = QPointF(
                    (event.position().x() - self.screen_rect.x()) / self.screen_rect.width(), 
                    (event.position().y() - self.screen_rect.y()) / self.screen_rect.height()
                )
                self.drag_start_pos = relative_pos_on_screen
                self.rect_start_pos = self.canvas_state.zoom_rect.topLeft()
                self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseMoveEvent(self, event):
        if not self.canvas_state or not self.is_dragging_lupa:
            return

        relative_pos_on_screen = QPointF(
            (event.position().x() - self.screen_rect.x()) / self.screen_rect.width(), 
            (event.position().y() - self.screen_rect.y()) / self.screen_rect.height()
        )

        delta_relative = relative_pos_on_screen - self.drag_start_pos
        
        new_rect = QRectF(self.canvas_state.zoom_rect)
        new_rect.moveTo(self.rect_start_pos + delta_relative)
        
        if new_rect.left() < 0: new_rect.moveLeft(0)
        if new_rect.top() < 0: new_rect.moveTop(0)
        if new_rect.right() > 1.0: new_rect.moveRight(1.0)
        if new_rect.bottom() > 1.0: new_rect.moveBottom(1.0)
        
        self.canvas_state.set_property('zoom_rect', new_rect)

    def mouseReleaseEvent(self, event):
        if self.is_dragging_lupa:
            self.is_dragging_lupa = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

