#!/usr/bin/env python3
# CloudQuest - Sistema de logging

import os
import logging
from datetime import datetime
from pathlib import Path

from config.settings import LOG_FILE

# Configuração global do logger
log = logging.getLogger("CloudQuest")

def setup_logger():
    """Configura o sistema de log da aplicação."""
    # Criar diretório de logs se não existir
    log_dir = Path(LOG_FILE).parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configuração do logger
    log.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                       datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    log.addHandler(file_handler)
    
    # Handler para console (opcional, útil para debugging)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                         datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    log.addHandler(console_handler)
    
    # Tentamos usar uma exceção para obter um rastreamento mais claro de onde o logger foi inicializado
    try:
        raise Exception("Logger setup")
    except Exception as e:
        log.debug(f"Logger inicializado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")