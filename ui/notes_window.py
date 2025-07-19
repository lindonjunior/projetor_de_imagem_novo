# ui/notes_window.py
# Certifique-se de que o PyQtWebEngine está instalado: pip install PyQtWebEngine
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from utils.html_generator import generate_html_with_dynamic_font

logger = logging.getLogger("ImageProjectorLogger")

class NotesWindow(QWidget):
    def __init__(self, screen):
        super().__init__()
        self.setWindowTitle("Anotações")
        
        logger.info(f"Inicializando NotesWindow na tela: {screen.name()}")

        # Configura para tela cheia
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(screen.geometry())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

    def update_text(self, text: str):
        """Atualiza o texto exibido na tela."""
        logger.debug(f"Atualizando NotesWindow com o texto: '{text[:30]}...'")
        html_content = generate_html_with_dynamic_font(text)
        self.webview.setHtml(html_content)

    def keyPressEvent(self, event):
        """Fecha a janela ao pressionar a tecla Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.logger.info("Tecla Esc pressionada na NotesWindow. Fechando.")
            self.close()

