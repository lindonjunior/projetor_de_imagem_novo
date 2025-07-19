# ui/widgets/thumbnail_list.py

import logging
from PySide6.QtWidgets import QListWidget, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

logger = logging.getLogger("ImageProjectorLogger")

class ThumbnailListWidget(QListWidget):
    """
    Um QListWidget especializado para exibir miniaturas de imagens
    com suporte a arrastar e soltar (drag-and-drop) para reordenação.
    """
    orderChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(128, 128))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setWordWrap(True)
        self.setMovement(QListWidget.Movement.Snap)
        self.setFlow(QListWidget.Flow.LeftToRight)
        
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        
        self.model().rowsMoved.connect(self.on_rows_moved)
        
    def populate_from_data(self, images_data):
        """
        Limpa a lista atual e a preenche com novos dados de imagem.
        """
        self.clear()
        for item_data in images_data:
            path = item_data['path']
            name = item_data['name']
            handler = item_data.get('handler')

            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            if handler:
                state = item_data.get('canvas_state')
                rotation = state.rotation if state else 0
                thumbnail_pixmap = handler.get_thumbnail_pixmap(self.iconSize(), rotation)
                if thumbnail_pixmap:
                    item.setIcon(QIcon(thumbnail_pixmap))
            
            self.addItem(item)
            
    def on_rows_moved(self, parent, start, end, destination, row):
        """
        Slot chamado quando o usuário termina de arrastar um item.
        """
        logger.info("Detectado Drag & Drop. Sincronizando lista de dados...")
        new_order_paths = [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]
        self.orderChanged.emit(new_order_paths)
        logger.info("Lista de dados sincronizada com sucesso.")


    def update_thumbnail_icon(self, index, pixmap):
        """
        Atualiza o ícone de um item específico na lista.
        """
        if 0 <= index < self.count():
            self.item(index).setIcon(QIcon(pixmap))

