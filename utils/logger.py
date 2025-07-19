# utils/logger.py

import logging
import os

# Define o diretório e o nome do arquivo de log
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger():
    """
    Configura um logger global para salvar em um arquivo e exibir no console.
    Esta versão apaga o log anterior a cada nova inicialização do programa.
    """
    # Garante que o diretório de logs exista
    os.makedirs(LOG_DIR, exist_ok=True)

    # Configuração do logger principal
    logger = logging.getLogger("ImageProjectorLogger")
    logger.setLevel(logging.DEBUG) # Captura todos os níveis de log para máximo detalhe

    # Evita adicionar múltiplos handlers se a função for chamada acidentalmente mais de uma vez
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formato do log: Data e Hora - Nível do Log - Módulo - Mensagem
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # --- FileHandler com modo 'w' para apagar o log anterior ---
    try:
        # O encoding='utf-8' é importante para suportar caracteres especiais
        file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Se houver um problema ao criar o arquivo de log, imprime no console
        print(f"Erro ao configurar o logger de arquivo: {e}")

    # --- StreamHandler para exibir logs no console ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

