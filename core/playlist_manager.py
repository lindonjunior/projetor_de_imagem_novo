# core/playlist_manager.py

import json
import logging
from PySide6.QtCore import QObject, QRectF
from core.canvas_state import CanvasState, DrawingStroke

logger = logging.getLogger("ImageProjectorLogger")

class PlaylistManager(QObject):
    """
    Gerencia o salvamento e carregamento de listas de reprodução (galerias).
    Uma playlist contém a lista de caminhos de imagem, seus nomes internos,
    e o estado de cada imagem (rotação, brilho, anotações, etc.).
    """
    def __init__(self):
        super().__init__()

    def save_playlist(self, images_data, file_path: str):
        """
        Salva a lista de imagens e seus estados em um arquivo JSON.

        Args:
            images_data (list): A lista de dicionários, cada um representando uma imagem.
            file_path (str): O caminho do arquivo .json onde a playlist será salva.
        """
        playlist_to_save = []
        for data in images_data:
            state = data['canvas_state']
            
            # Serializa os desenhos
            strokes_to_save = []
            if state.strokes:
                for stroke in state.strokes:
                    points = []
                    for i in range(stroke.path.elementCount()):
                        el = stroke.path.elementAt(i)
                        points.append({'x': el.x, 'y': el.y})
                    
                    strokes_to_save.append({
                        'points': points,
                        'color': stroke.color.name(),
                        'thickness': stroke.thickness
                    })

            state_dict = {
                'rotation': state.rotation,
                'brightness': state.brightness,
                'contrast_applied': state.contrast_applied,
                'display_mode': state.display_mode,
                'zoom_enabled': state.zoom_enabled,
                'zoom_rect': [state.zoom_rect.x(), state.zoom_rect.y(), state.zoom_rect.width(), state.zoom_rect.height()],
                'strokes': strokes_to_save,
                'projection_aspect_ratio': state.projection_aspect_ratio
            }
            
            playlist_to_save.append({
                'path': data['path'],
                'name': data['name'],
                'state': state_dict
            })

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_to_save, f, indent=4)
            logger.info(f"Playlist salva com sucesso em: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Falha ao salvar a playlist em {file_path}", exc_info=True)
            return False

    def load_playlist(self, file_path: str):
        """
        Carrega uma playlist de um arquivo JSON.

        Args:
            file_path (str): O caminho do arquivo .json da playlist.

        Returns:
            list: Uma lista de dicionários de imagem pronta para ser usada pela MainWindow,
                  ou uma lista vazia em caso de falha.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            images_data = []
            for item in loaded_data:
                state = CanvasState()
                state_dict = item.get('state', {})
                state.rotation = state_dict.get('rotation', 0)
                state.brightness = state_dict.get('brightness', 1.0)
                state.contrast_applied = state_dict.get('contrast_applied', False)
                state.display_mode = state_dict.get('display_mode', "Ajustar (Fit)")
                state.zoom_enabled = state_dict.get('zoom_enabled', False)
                
                zoom_rect_data = state_dict.get('zoom_rect', [0.25, 0.25, 0.5, 0.28125])
                state.zoom_rect = QRectF(*zoom_rect_data)
                
                state.projection_aspect_ratio = state_dict.get('projection_aspect_ratio', 16.0 / 9.0)

                # Carrega os desenhos
                loaded_strokes = state_dict.get('strokes', [])
                from PySide6.QtGui import QPainterPath, QColor
                from PySide6.QtCore import QPointF

                for stroke_data in loaded_strokes:
                    path = QPainterPath()
                    points = stroke_data.get('points', [])
                    if points:
                        path.moveTo(QPointF(points[0]['x'], points[0]['y']))
                        for i in range(1, len(points)):
                            path.lineTo(QPointF(points[i]['x'], points[i]['y']))
                    
                    color = QColor(stroke_data.get('color', '#ff0000'))
                    thickness = stroke_data.get('thickness', 5.0)
                    state.strokes.append(DrawingStroke(path, color, thickness))

                images_data.append({
                    'path': item['path'],
                    'name': item['name'],
                    'canvas_state': state
                })
            
            logger.info(f"Playlist carregada de: {file_path}")
            return images_data
        except Exception as e:
            logger.error(f"Falha ao carregar a playlist de {file_path}", exc_info=True)
            return []

