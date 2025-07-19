# main.py

import sys
import logging
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import setup_logger # Importa nossa função de setup

if __name__ == "__main__":
    # 1. Configura o logger assim que o programa inicia
    app_logger = setup_logger()
    
    try:
        app_logger.info("=====================================")
        app_logger.info("      Iniciando Nova Sessão")
        app_logger.info("=====================================")

        app = QApplication(sys.argv)
        
        # Adiciona um estilo básico para melhorar a aparência
        app.setStyle("Fusion")

        # 2. Passa o logger para a janela principal
        main_win = MainWindow(logger=app_logger)
        main_win.show()
        
        sys.exit(app.exec())

    except Exception as e:
        # Captura qualquer erro fatal que não foi tratado e o registra
        app_logger.critical("Ocorreu um erro fatal e a aplicação será encerrada.", exc_info=True)
        sys.exit(1)

