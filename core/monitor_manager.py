# core/monitor_manager.py
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QScreen

logger = logging.getLogger("ImageProjectorLogger")

def get_available_screens() -> list[QScreen]:
    """Retorna uma lista de todos os monitores conectados (QScreen)."""
    screens = QApplication.screens()
    logger.debug(f"Detectados {len(screens)} monitores.")
    return screens

def get_primary_screen() -> QScreen | None:
    """Retorna o monitor principal do sistema."""
    primary = QApplication.primaryScreen()
    if primary:
        logger.debug(f"Monitor principal detectado: {primary.name()}")
    else:
        logger.warning("Nenhum monitor principal encontrado.")
    return primary

def get_secondary_screen() -> QScreen | None:
    """Retorna o primeiro monitor que não é o principal, se existir."""
    screens = get_available_screens()
    primary = get_primary_screen()
    
    if len(screens) <= 1:
        logger.info("Nenhum monitor secundário encontrado.")
        return None

    for screen in screens:
        if screen != primary:
            logger.info(f"Monitor secundário encontrado: {screen.name()}")
            return screen
            
    logger.warning("Não foi possível determinar um monitor secundário apesar de múltiplos monitores estarem presentes.")
    # Se não encontrar um diferente, retorna o último da lista que não seja o primário (caso haja mais de 2)
    if screens and screens[-1] != primary:
        return screens[-1]
    return None

