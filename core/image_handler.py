# core/image_handler.py

import logging
from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QSize, QRectF

logger = logging.getLogger("ImageProjectorLogger")

class ImageHandler:
    def __init__(self, file_path: str):
        try:
            self.original_image = Image.open(file_path).convert("RGBA")
        except Exception as e:
            logger.error(f"Falha ao carregar a imagem: {file_path}", exc_info=True)
            self.original_image = None

    def _pil_to_qpixmap(self, pil_image: Image) -> QPixmap:
        try:
            data = pil_image.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
            return QPixmap.fromImage(qimage)
        except Exception as e:
            logger.error(f"Erro ao converter imagem PIL para QPixmap: {e}", exc_info=True)
            return QPixmap()

    def _draw_strokes_on_image(self, image: Image, strokes: list) -> Image:
        if not strokes:
            return image
        image_with_drawings = image.copy()
        draw = ImageDraw.Draw(image_with_drawings)
        img_w, img_h = image.size
        for stroke in strokes:
            points = []
            for i in range(stroke.path.elementCount()):
                el = stroke.path.elementAt(i)
                points.append((el.x * img_w, el.y * img_h))
            if len(points) > 1:
                color_tuple = (stroke.color.red(), stroke.color.green(), stroke.color.blue(), stroke.color.alpha())
                draw.line(points, fill=color_tuple, width=int(stroke.thickness), joint="curve")
        return image_with_drawings

    def get_processed_pixmap_for_preview(self, state):
        if not self.original_image: return None
        processed_image = self.original_image
        if state.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(processed_image)
            processed_image = enhancer.enhance(state.brightness)
        if state.contrast_applied:
            processed_image_rgb = processed_image.convert("RGB")
            contrasted_image = ImageOps.autocontrast(processed_image_rgb)
            processed_image = contrasted_image.convert("RGBA")
        if state.rotation != 0:
            processed_image = processed_image.rotate(state.rotation, expand=True)
        return self._pil_to_qpixmap(processed_image)

    def get_processed_pixmap_for_projection(self, state, crop_info: dict | None):
        if not self.original_image: return None
        
        processed_image = self.original_image
        
        if state.strokes:
            processed_image = self._draw_strokes_on_image(processed_image, state.strokes)

        if crop_info:
            crop_rect = crop_info.get("crop_rect")
            final_rotation = crop_info.get("final_rotation", 0)

            # --- CORREÇÃO: Pipeline Crop -> Rotate ---
            if crop_rect and crop_rect.isValid():
                left = int(crop_rect.left())
                top = int(crop_rect.top())
                right = int(crop_rect.right())
                bottom = int(crop_rect.bottom())
                
                # Garante que a área de corte não exceda as dimensões da imagem
                if right > processed_image.width: right = processed_image.width
                if bottom > processed_image.height: bottom = processed_image.height

                processed_image = processed_image.crop((left, top, right, bottom))
            
            # Aplica a rotação final APÓS o corte
            if final_rotation != 0:
                processed_image = processed_image.rotate(final_rotation, expand=True, fillcolor=(0,0,0,0))
        else:
            # Se não houver zoom, aplica apenas a rotação da imagem
            if state.rotation != 0:
                 processed_image = processed_image.rotate(state.rotation, expand=True, fillcolor=(0,0,0,0))


        # Efeitos são aplicados após a transformação
        if state.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(processed_image)
            processed_image = enhancer.enhance(state.brightness)
        if state.contrast_applied:
            processed_image_rgb = processed_image.convert("RGB")
            contrasted_image = ImageOps.autocontrast(processed_image_rgb)
            processed_image = contrasted_image.convert("RGBA")

        return self._pil_to_qpixmap(processed_image)

    def get_thumbnail_pixmap(self, size: QSize, rotation_angle=0):
        if not self.original_image: return None
        thumbnail_image = self.original_image.copy()
        thumbnail_image.thumbnail((size.width(), size.height()), Image.Resampling.LANCZOS)
        if rotation_angle != 0:
            thumbnail_image = thumbnail_image.rotate(rotation_angle, expand=True)
        return self._pil_to_qpixmap(thumbnail_image)

