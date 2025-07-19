# ui/main_window.py

import os
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QComboBox, QApplication, QFileDialog, QSlider, QLabel,
                               QListWidgetItem, QColorDialog, QLineEdit, QGroupBox,
                               QSplitter, QCheckBox, QToolButton, QButtonGroup,
                               QAbstractButton, QMessageBox)
from PySide6.QtCore import Slot, Qt, QSize, QRectF, QPointF
from PySide6.QtGui import QIcon, QScreen, QTransform

from core.monitor_manager import get_available_screens, get_secondary_screen
from core.image_handler import ImageHandler
from core.canvas_state import CanvasState
from core.playlist_manager import PlaylistManager
from ui.projection_window import ProjectionWindow
from ui.notes_window import NotesWindow
from ui.widgets.zoom_preview import ZoomPreview
from ui.widgets.thumbnail_list import ThumbnailListWidget

class MainWindow(QMainWindow):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.setWindowTitle("Visor de Imagens - Painel do Operador")
        
        self.projection_win = None
        self.notes_win = None
        self.images_data = [] 
        self.current_image_index = -1
        self.playlist_manager = PlaylistManager()
        self.current_canvas_state = None
        
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.setup_ui_elements()
        self.connect_signals()
        
        primary_screen = QApplication.primaryScreen()
        if primary_screen: self.move(primary_screen.geometry().topLeft())
        self.resize(1280, 800)
        
        self.update_monitor_state()

    def setup_ui_elements(self):
        # UI Elements setup is omitted for brevity as it's unchanged.
        # Barra Superior
        top_bar_layout = QHBoxLayout()
        self.browse_folder_button = QPushButton("Buscar Pasta...")
        self.load_playlist_button = QPushButton("Carregar Galeria...")
        self.save_playlist_button = QPushButton("Salvar Galeria")
        self.prev_button = QPushButton("Anterior")
        self.next_button = QPushButton("Próximo")
        top_bar_layout.addWidget(self.browse_folder_button)
        top_bar_layout.addWidget(self.load_playlist_button)
        top_bar_layout.addWidget(self.save_playlist_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.prev_button)
        top_bar_layout.addWidget(self.next_button)

        # Painel Principal (Dividido)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.thumbnail_list = ThumbnailListWidget()
        main_splitter.addWidget(self.thumbnail_list)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.zoom_preview_widget = ZoomPreview()
        right_layout.addWidget(self.zoom_preview_widget, stretch=1)

        # Controles de Zoom
        zoom_controls_group = QGroupBox("Controle de Zoom")
        zoom_controls_layout = QVBoxLayout(zoom_controls_group)
        
        zoom_actions_layout = QHBoxLayout()
        self.zoom_enabled_checkbox = QCheckBox("Ativar Zoom")
        self.rotate_lupa_button = QPushButton("Girar Lupa")
        zoom_actions_layout.addWidget(self.zoom_enabled_checkbox)
        zoom_actions_layout.addWidget(self.rotate_lupa_button)
        
        zoom_slider_layout = QHBoxLayout()
        zoom_slider_layout.addWidget(QLabel("Tamanho da Lupa:"))
        self.zoom_factor_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_factor_slider.setRange(10, 100)
        self.zoom_factor_slider.setValue(50)
        zoom_slider_layout.addWidget(self.zoom_factor_slider)
        
        zoom_controls_layout.addLayout(zoom_actions_layout)
        zoom_controls_layout.addLayout(zoom_slider_layout)
        right_layout.addWidget(zoom_controls_group)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 800])

        # Ferramentas de Desenho
        drawing_toolbar = QHBoxLayout()
        drawing_toolbar.addWidget(QLabel("Ferramentas:"))
        self.pen_button = QToolButton(); self.pen_button.setText("Caneta"); self.pen_button.setCheckable(True)
        self.highlighter_button = QToolButton(); self.highlighter_button.setText("Marca-Texto"); self.highlighter_button.setCheckable(True)
        self.laser_button = QToolButton(); self.laser_button.setText("Laser"); self.laser_button.setCheckable(True)
        self.clear_drawings_button = QPushButton("Limpar Desenhos")
        self.tool_button_group = QButtonGroup(self)
        self.tool_button_group.setExclusive(True)
        self.tool_button_group.addButton(self.pen_button)
        self.tool_button_group.addButton(self.highlighter_button)
        self.tool_button_group.addButton(self.laser_button)
        drawing_toolbar.addWidget(self.pen_button); drawing_toolbar.addWidget(self.highlighter_button); drawing_toolbar.addWidget(self.laser_button); drawing_toolbar.addStretch(); drawing_toolbar.addWidget(self.clear_drawings_button)

        # Gerenciamento de Imagem
        management_layout = QHBoxLayout()
        management_layout.addWidget(QLabel("Nome Interno:"))
        self.rename_edit = QLineEdit()
        self.sort_by_name_button = QPushButton("Ordenar por Nome")
        self.sort_by_original_name_button = QPushButton("Ordenar por Original")
        management_layout.addWidget(self.rename_edit); management_layout.addWidget(self.sort_by_name_button); management_layout.addWidget(self.sort_by_original_name_button)

        # Controles de Exibição
        display_controls_layout = QHBoxLayout()
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(QLabel("Modo de Exibição:"))
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(ProjectionWindow.DISPLAY_MODES.keys())
        mode_layout.addWidget(self.display_mode_combo)
        self.bg_color_button = QPushButton("Cor de Fundo")
        display_controls_layout.addLayout(mode_layout); display_controls_layout.addWidget(self.bg_color_button); display_controls_layout.addStretch()

        # Ajustes de Imagem
        self.adjustments_group = QGroupBox("Ajustes de Imagem")
        adjustments_layout = QVBoxLayout(self.adjustments_group)
        brightness_hbox = QHBoxLayout()
        self.brightness_label = QLabel("Brilho: 100%")
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(20, 200); self.brightness_slider.setValue(100)
        brightness_hbox.addWidget(self.brightness_label); brightness_hbox.addWidget(self.brightness_slider)
        other_adjustments_hbox = QHBoxLayout()
        self.rotate_button = QPushButton("Girar Imagem 90°")
        self.auto_contrast_button = QPushButton("Contraste Automático")
        self.undo_contrast_button = QPushButton("Desfazer Contraste"); self.undo_contrast_button.setVisible(False)
        other_adjustments_hbox.addWidget(self.rotate_button); other_adjustments_hbox.addWidget(self.auto_contrast_button); other_adjustments_hbox.addWidget(self.undo_contrast_button); other_adjustments_hbox.addStretch()
        adjustments_layout.addLayout(brightness_hbox); adjustments_layout.addLayout(other_adjustments_hbox)
        
        # Controles de Projeção
        projection_controls_layout = QHBoxLayout()
        projection_controls_layout.addWidget(QLabel("Monitor de Projeção:"))
        self.monitor_combo = QComboBox()
        self.project_button = QPushButton("▶️ Projetar")
        self.project_button.setObjectName("ProjectButton")
        projection_controls_layout.addWidget(self.monitor_combo); projection_controls_layout.addWidget(self.project_button)
        
        # Controles de Anotações
        notes_controls_layout = QHBoxLayout()
        notes_controls_layout.addWidget(QLabel("Monitor de Anotações:"))
        self.notes_monitor_combo = QComboBox()
        self.toggle_notes_button = QPushButton("Ativar Anotações")
        self.toggle_notes_button.setCheckable(True)
        notes_controls_layout.addWidget(self.notes_monitor_combo)
        notes_controls_layout.addWidget(self.toggle_notes_button)

        # Adiciona tudo ao layout principal
        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addWidget(main_splitter, stretch=1)
        self.main_layout.addLayout(drawing_toolbar)
        self.main_layout.addLayout(management_layout)
        self.main_layout.addLayout(display_controls_layout)
        self.main_layout.addWidget(self.adjustments_group)
        self.main_layout.addLayout(projection_controls_layout)
        self.main_layout.addLayout(notes_controls_layout)
        
        self.update_controls_state()

    def connect_signals(self):
        self.project_button.clicked.connect(self.toggle_projection)
        self.tool_button_group.buttonClicked.connect(self.on_tool_button_clicked)
        self.clear_drawings_button.clicked.connect(self.clear_current_drawings)
        self.browse_folder_button.clicked.connect(self.browse_folder)
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        self.prev_button.clicked.connect(self.previous_image)
        self.next_button.clicked.connect(self.next_image)
        self.rotate_button.clicked.connect(self.rotate_image)
        self.rotate_lupa_button.clicked.connect(self.rotate_lupa)
        self.brightness_slider.valueChanged.connect(self.change_brightness)
        self.display_mode_combo.currentTextChanged.connect(self.on_display_mode_changed)
        self.bg_color_button.clicked.connect(self.select_background_color)
        self.rename_edit.editingFinished.connect(self.rename_current_image)
        self.sort_by_name_button.clicked.connect(lambda: self.sort_images_by('name'))
        self.sort_by_original_name_button.clicked.connect(lambda: self.sort_images_by('path'))
        self.auto_contrast_button.clicked.connect(self.apply_auto_contrast)
        self.undo_contrast_button.clicked.connect(self.undo_auto_contrast)
        self.zoom_enabled_checkbox.toggled.connect(self.on_zoom_enabled_toggled)
        self.zoom_factor_slider.valueChanged.connect(self.on_zoom_factor_changed)
        self.load_playlist_button.clicked.connect(self.load_playlist)
        self.save_playlist_button.clicked.connect(self.save_playlist)
        self.thumbnail_list.orderChanged.connect(self.on_thumbnail_order_changed)
        
        app = QApplication.instance()
        if app:
            app.screenAdded.connect(self.update_monitor_state)
            app.screenRemoved.connect(self.update_monitor_state)
        
        self.monitor_combo.currentIndexChanged.connect(self.on_monitor_changed)
        self.toggle_notes_button.toggled.connect(self.toggle_notes_window)

    @Slot()
    def save_playlist(self):
        if not self.images_data:
            QMessageBox.warning(self, "Galeria Vazia", "Não há imagens na galeria para salvar.")
            return
        filePath, _ = QFileDialog.getSaveFileName(self, "Salvar Galeria", "", "Arquivos JSON (*.json)")
        if filePath:
            if not filePath.endswith('.json'): filePath += '.json'
            if self.playlist_manager.save_playlist(self.images_data, filePath):
                QMessageBox.information(self, "Sucesso", "Galeria salva com sucesso!")
            else:
                QMessageBox.critical(self, "Erro", "Ocorreu um erro ao salvar a galeria.")

    @Slot()
    def load_playlist(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Carregar Galeria", "", "Arquivos JSON (*.json)")
        if filePath:
            loaded_data = self.playlist_manager.load_playlist(filePath)
            if not loaded_data:
                QMessageBox.critical(self, "Erro", "Não foi possível carregar o arquivo da galeria.")
                return
            self.images_data = []
            self.current_image_index = -1
            for item_data in loaded_data:
                if os.path.exists(item_data['path']):
                    item_data['handler'] = ImageHandler(item_data['path'])
                    self.images_data.append(item_data)
                else:
                    self.logger.warning(f"Imagem não encontrada, pulando: {item_data['path']}")
            self.repopulate_thumbnail_list()
            self.update_controls_state()
            if self.images_data: self.load_image_by_index(0)

    def repopulate_thumbnail_list(self):
        current_selection_path = None
        if 0 <= self.current_image_index < len(self.images_data):
            current_selection_path = self.images_data[self.current_image_index]['path']
        self.thumbnail_list.populate_from_data(self.images_data)
        if current_selection_path:
            for i, data in enumerate(self.images_data):
                if data['path'] == current_selection_path:
                    self.thumbnail_list.setCurrentRow(i)
                    self.current_image_index = i
                    break
    
    @Slot(list)
    def on_thumbnail_order_changed(self, new_path_order: list):
        if not self.images_data: return
        
        current_path = None
        if self.current_image_index != -1:
            current_path = self.images_data[self.current_image_index]['path']

        data_map = {item['path']: item for item in self.images_data}
        self.images_data = [data_map[path] for path in new_path_order if path in data_map]
        
        if current_path:
            for i, data in enumerate(self.images_data):
                if data['path'] == current_path:
                    self.current_image_index = i
                    self.thumbnail_list.blockSignals(True)
                    self.thumbnail_list.setCurrentRow(i)
                    self.thumbnail_list.blockSignals(False)
                    break
    
    @Slot()
    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Imagens")
        if folder_path:
            self.images_data = []
            self.current_image_index = -1
            supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')
            filenames = sorted(os.listdir(folder_path))
            for filename in filenames:
                if filename.lower().endswith(supported_formats):
                    full_path = os.path.join(folder_path, filename)
                    self.images_data.append({'path': full_path, 'name': filename, 'handler': ImageHandler(full_path), 'canvas_state': CanvasState()})
            self.repopulate_thumbnail_list()
            self.update_controls_state()
            if self.images_data: self.load_image_by_index(0)

    def _get_current_state(self):
        if 0 <= self.current_image_index < len(self.images_data):
            return self.images_data[self.current_image_index]['canvas_state']
        return None

    def _refresh_all_displays(self):
        if self.current_image_index == -1: return
        state = self._get_current_state()
        handler = self.images_data[self.current_image_index]['handler']
        
        base_pixmap_for_preview = handler.get_processed_pixmap_for_preview(state)
        if base_pixmap_for_preview:
            self.zoom_preview_widget.set_canvas_state(state, base_pixmap_for_preview)
        
        self.redraw_current_thumbnail()
        self.update_projection()

    @Slot()
    def _update_laser_only(self):
        self.zoom_preview_widget.update()
        if self.projection_win: self.projection_win.update()

    def update_projection(self):
        if self.current_image_index == -1 or self.projection_win is None: return
        state = self._get_current_state()
        handler = self.images_data[self.current_image_index]['handler']
        
        crop_info = self._calculate_crop_info(state, handler) if state.zoom_enabled else None
        
        final_pixmap = handler.get_processed_pixmap_for_projection(state, crop_info)
        self.projection_win.update_display(final_pixmap, state)

    def load_image_by_index(self, index):
        if not (0 <= index < len(self.images_data)): return
        
        if self.current_canvas_state:
            try:
                self.current_canvas_state.state_changed.disconnect(self._refresh_all_displays)
                self.current_canvas_state.laser_position_changed.disconnect(self._update_laser_only)
            except RuntimeError: pass

        self.current_image_index = index
        self.thumbnail_list.setCurrentRow(index)
        
        state = self._get_current_state()
        self.current_canvas_state = state
        
        if self.current_canvas_state:
            self.current_canvas_state.state_changed.connect(self._refresh_all_displays)
            self.current_canvas_state.laser_position_changed.connect(self._update_laser_only)
        
        self.on_monitor_changed()

        self.brightness_slider.setValue(int(state.brightness * 100))
        self.rename_edit.setText(self.images_data[index]['name'])
        self.display_mode_combo.setCurrentText(state.display_mode)
        self.update_contrast_buttons_visibility(state.contrast_applied)
        
        self.zoom_enabled_checkbox.blockSignals(True)
        self.zoom_factor_slider.blockSignals(True)
        self.zoom_enabled_checkbox.setChecked(state.zoom_enabled)
        
        slider_value = int(state.zoom_rect.width() * 100)
        self.zoom_factor_slider.setValue(slider_value)

        self.zoom_enabled_checkbox.blockSignals(False)
        self.zoom_factor_slider.blockSignals(False)
        
        if self.tool_button_group.checkedButton():
            self.tool_button_group.checkedButton().setChecked(False)
        state.set_property('active_tool', "none")
        
        self.update_controls_state()
        self._refresh_all_displays()

    def keyPressEvent(self, event):
        if QApplication.focusWidget() in [self.rename_edit]:
            super().keyPressEvent(event)
            return
            
        key = event.key()
        if key == Qt.Key.Key_Escape: self.toggle_projection()
        elif key in [Qt.Key.Key_Right, Qt.Key.Key_PageDown]: self.next_image()
        elif key in [Qt.Key.Key_Left, Qt.Key.Key_PageUp]: self.previous_image()
        else: super().keyPressEvent(event)

    @Slot()
    def toggle_projection(self):
        if self.projection_win is not None:
            self.logger.info("Ação: RECOLHER.")
            self.projection_win.close()
            return

        self.logger.info("Ação: PROJETAR.")
        if self.current_image_index == -1:
            self.logger.warning("Nenhuma imagem selecionada. Ação cancelada.")
            return

        selected_screen = self.monitor_combo.currentData()
        if not selected_screen:
            self.logger.warning("Nenhum monitor selecionado. Ação cancelada.")
            QMessageBox.warning(self, "Nenhum Monitor", "Nenhum monitor de projeção selecionado.")
            return
            
        self.projection_win = ProjectionWindow(screen=selected_screen)
        self.projection_win.destroyed.connect(self.on_projection_destroyed_safeguard)
        
        self.project_button.setText("⏹️ Recolher")
        self.update_controls_state()
        self.projection_win.showFullScreen()
        self.update_projection()
        self.logger.info("Projeção concluída com sucesso.")

    @Slot()
    def on_projection_destroyed_safeguard(self):
        self.logger.warning("--- Sinal 'destroyed' (salvaguarda) recebido. ---")
        if self.projection_win is not None:
            try:
                self.projection_win.destroyed.disconnect(self.on_projection_destroyed_safeguard)
            except RuntimeError:
                pass
            self.projection_win = None
        
        self.project_button.setText("▶️ Projetar")
        self.update_controls_state()
        self.logger.info("Estado resetado para 'recolhido'.")

    @Slot()
    def update_monitor_state(self):
        self.populate_monitors(self.monitor_combo)
        self.populate_monitors(self.notes_monitor_combo)
        
        if self.monitor_combo.count() == 0:
            self.zoom_preview_widget.show_message("Nenhum monitor externo detectado.")
        else:
            self.on_monitor_changed()

    @Slot()
    def on_monitor_changed(self):
        selected_screen = self.monitor_combo.currentData()
        if isinstance(selected_screen, QScreen):
            size = selected_screen.size()
            aspect_ratio = size.width() / size.height() if size.height() > 0 else 16.0 / 9.0
            self.logger.info(f"Monitor de projeção alterado para '{selected_screen.name()}'. Nova proporção: {aspect_ratio:.2f}")

            self.zoom_preview_widget.set_aspect_ratio(aspect_ratio)
            state = self._get_current_state()
            if state:
                state.set_property('projection_aspect_ratio', aspect_ratio)
            
            self.on_zoom_factor_changed(self.zoom_factor_slider.value())
            self._refresh_all_displays()
        else:
            self.zoom_preview_widget.show_message("Conecte um monitor e selecione-o para projeção.")
            self.logger.warning("Nenhum monitor de projeção válido selecionado.")

    def populate_monitors(self, combo_box):
        self.logger.info(f"Atualizando a lista de monitores para {combo_box.objectName()}...")
        current_screen_name = combo_box.currentText()
        combo_box.blockSignals(True)
        combo_box.clear()
        
        screens = get_available_screens()
        
        for screen in screens:
            combo_box.addItem(f"{screen.name()} ({screen.size().width()}x{screen.size().height()})", screen)
        
        index = combo_box.findText(current_screen_name)
        if index != -1:
            combo_box.setCurrentIndex(index)
        elif combo_box is self.monitor_combo:
            secondary_screen = get_secondary_screen()
            if secondary_screen:
                index = combo_box.findData(secondary_screen)
                if index != -1:
                    combo_box.setCurrentIndex(index)

        combo_box.blockSignals(False)

    def _calculate_crop_info(self, state: CanvasState, handler: ImageHandler) -> dict | None:
        # --- CORREÇÃO: Esta função agora retorna o retângulo de corte e a rotação final ---
        if not handler.original_image: return None
        
        img_w, img_h = handler.original_image.size
        
        # 1. Obter retângulo da lupa em coordenadas da pré-visualização (pixels)
        preview_rect = self.zoom_preview_widget.screen_rect
        lupa_rect_preview_unrotated = QRectF(
            preview_rect.x() + state.zoom_rect.x() * preview_rect.width(),
            preview_rect.y() + state.zoom_rect.y() * preview_rect.height(),
            state.zoom_rect.width() * preview_rect.width(),
            state.zoom_rect.height() * preview_rect.height()
        )

        # 2. Obter os 4 cantos da lupa e aplicar a rotação da lupa
        lupa_center_abs = lupa_rect_preview_unrotated.center()
        transform_lupa = QTransform().translate(lupa_center_abs.x(), lupa_center_abs.y()).rotate(state.lupa_rotation).translate(-lupa_center_abs.x(), -lupa_center_abs.y())
        lupa_corners_rotated = transform_lupa.mapToPolygon(lupa_rect_preview_unrotated.toRect())
        
        # 3. Criar a matriz de transformação da tela para a imagem original
        image_on_screen_rect = self.zoom_preview_widget.image_on_screen_rect
        
        transform_img_to_screen = QTransform()
        transform_img_to_screen.translate(image_on_screen_rect.center().x(), image_on_screen_rect.center().y())
        transform_img_to_screen.rotate(state.rotation)
        transform_img_to_screen.scale(image_on_screen_rect.width() / img_w, image_on_screen_rect.height() / img_h)
        transform_img_to_screen.translate(-img_w / 2, -img_h / 2)
        
        inverse_transform, invertible = transform_img_to_screen.inverted()
        if not invertible:
            self.logger.error("Matriz de transformação não é invertível.")
            return None

        # 4. Mapear os cantos da lupa para o espaço da imagem original
        original_corners = [inverse_transform.map(p) for p in lupa_corners_rotated]
        
        # 5. Calcular o bounding box dos cantos transformados
        min_x = min(p.x() for p in original_corners)
        max_x = max(p.x() for p in original_corners)
        min_y = min(p.y() for p in original_corners)
        max_y = max(p.y() for p in original_corners)
        
        crop_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        
        # 6. Calcular a rotação final para o handler
        final_rotation = (state.rotation - state.lupa_rotation) % 360

        return {
            "crop_rect": crop_rect,
            "final_rotation": final_rotation
        }

    def update_controls_state(self):
        has_images = bool(self.images_data)
        has_selection = self.current_image_index != -1
        is_projecting = self.projection_win is not None

        self.prev_button.setEnabled(has_selection)
        self.next_button.setEnabled(has_selection)
        self.save_playlist_button.setEnabled(has_images)
        self.sort_by_name_button.setEnabled(has_images)
        self.sort_by_original_name_button.setEnabled(has_images)
        
        self.adjustments_group.setEnabled(has_selection)
        self.zoom_preview_widget.setEnabled(has_selection)
        self.rename_edit.setEnabled(has_selection)
        self.clear_drawings_button.setEnabled(has_selection)
        self.pen_button.setEnabled(has_selection)
        self.highlighter_button.setEnabled(has_selection)
        self.laser_button.setEnabled(has_selection)
        self.rotate_lupa_button.setEnabled(has_selection)

        self.project_button.setEnabled(has_selection and self.monitor_combo.count() > 0)
        self.display_mode_combo.setEnabled(is_projecting)
        self.bg_color_button.setEnabled(is_projecting)

        self.toggle_notes_button.setEnabled(has_selection and self.notes_monitor_combo.count() > 0)

    def redraw_current_thumbnail(self):
        if self.current_image_index == -1: return
        item_data = self.images_data[self.current_image_index]
        handler, state = item_data['handler'], item_data['canvas_state']
        pixmap = handler.get_thumbnail_pixmap(self.thumbnail_list.iconSize(), state.rotation)
        if pixmap: self.thumbnail_list.update_thumbnail_icon(self.current_image_index, pixmap)

    def sort_images_by(self, key_to_sort):
        if not self.images_data: return
        current_path = None
        if self.current_image_index != -1:
            current_path = self.images_data[self.current_image_index]['path']
        if key_to_sort == 'path':
            self.images_data.sort(key=lambda item: os.path.basename(item['path']).lower())
        else:
            self.images_data.sort(key=lambda item: item['name'].lower())
        self.repopulate_thumbnail_list()
        if current_path:
            for i, data in enumerate(self.images_data):
                if data['path'] == current_path:
                    self.load_image_by_index(i)
                    break

    @Slot(QListWidgetItem)
    def on_thumbnail_clicked(self, item):
        item_path = item.data(Qt.ItemDataRole.UserRole)
        for i, data in enumerate(self.images_data):
            if data['path'] == item_path:
                self.load_image_by_index(i)
                break

    @Slot()
    def next_image(self):
        if not self.images_data: return
        self.load_image_by_index((self.current_image_index + 1) % len(self.images_data))

    @Slot()
    def previous_image(self):
        if not self.images_data: return
        self.load_image_by_index((self.current_image_index - 1 + len(self.images_data)) % len(self.images_data))

    @Slot()
    def rotate_image(self):
        state = self._get_current_state()
        if state: state.set_property('rotation', (state.rotation + 90) % 360)

    @Slot()
    def rotate_lupa(self):
        state = self._get_current_state()
        if state:
            state.set_property('lupa_rotation', (state.lupa_rotation + 90) % 180) # Alterna entre 0 e 90
            self.on_zoom_factor_changed(self.zoom_factor_slider.value())

    @Slot(int)
    def change_brightness(self, value):
        self.brightness_label.setText(f"Brilho: {value}%")
        state = self._get_current_state()
        if state: state.set_property('brightness', value / 100.0)

    @Slot(QAbstractButton)
    def on_tool_button_clicked(self, clicked_button):
        state = self._get_current_state()
        if not state: return
        tool_map = {self.pen_button: "pen", self.highlighter_button: "highlighter", self.laser_button: "laser"}
        if clicked_button and clicked_button.isChecked():
            new_tool = tool_map.get(clicked_button, "none")
            state.set_property('active_tool', new_tool)
        else:
            state.set_property('active_tool', "none")

    @Slot()
    def clear_current_drawings(self):
        state = self._get_current_state()
        if state: state.clear_drawings()

    @Slot()
    def select_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid() and self.projection_win is not None:
            self.projection_win.set_background_color(color.name())

    @Slot()
    def rename_current_image(self):
        if self.current_image_index != -1 and self.rename_edit.text():
            new_name = self.images_data[self.current_image_index]['name'] = self.rename_edit.text()
            self.thumbnail_list.item(self.current_image_index).setText(new_name)

    @Slot(bool)
    def on_zoom_enabled_toggled(self, checked):
        state = self._get_current_state()
        if state: state.set_property('zoom_enabled', checked)

    @Slot(int)
    def on_zoom_factor_changed(self, value):
        factor = value / 100.0
        state = self._get_current_state()
        if not state: return
        
        center = state.zoom_rect.center()
        
        # --- CORREÇÃO DEFINITIVA: Lógica da Proporção da Lupa ---
        new_width = factor
        new_height = factor
        
        new_rect = QRectF(0, 0, new_width, new_height)
        new_rect.moveCenter(center)
        
        if new_rect.left() < 0: new_rect.moveLeft(0)
        if new_rect.top() < 0: new_rect.moveTop(0)
        if new_rect.right() > 1.0: new_rect.moveRight(1.0)
        if new_rect.bottom() > 1.0: new_rect.moveBottom(1.0)
        
        state.set_property('zoom_rect', new_rect)

    @Slot(str)
    def on_display_mode_changed(self, mode_name):
        state = self._get_current_state()
        if state: state.set_property('display_mode', mode_name)

    @Slot()
    def apply_auto_contrast(self):
        state = self._get_current_state()
        if state:
            state.set_property('contrast_applied', True)
            self.update_contrast_buttons_visibility(True)

    @Slot()
    def undo_auto_contrast(self):
        state = self._get_current_state()
        if state:
            state.set_property('contrast_applied', False)
            self.update_contrast_buttons_visibility(False)

    def update_contrast_buttons_visibility(self, contrast_is_applied):
        self.auto_contrast_button.setVisible(not contrast_is_applied)
        self.undo_contrast_button.setVisible(contrast_is_applied)

    @Slot(bool)
    def toggle_notes_window(self, checked):
        if not checked:
            if self.notes_win:
                self.notes_win.close()
            return

        selected_screen = self.notes_monitor_combo.currentData()
        if not isinstance(selected_screen, QScreen):
            QMessageBox.warning(self, "Nenhum Monitor", "Nenhum monitor de anotações selecionado.")
            self.toggle_notes_button.setChecked(False)
            return
        
        self.notes_win = NotesWindow(screen=selected_screen)
        self.notes_win.destroyed.connect(self.on_notes_destroyed)
        self.notes_win.showFullScreen()

    @Slot()
    def on_notes_destroyed(self):
        self.notes_win = None
        self.toggle_notes_button.setChecked(False)

