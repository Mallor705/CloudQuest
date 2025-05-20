#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Sistema de logging.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Configuracao global do logger
log = logging.getLogger("CloudQuest")

def setup_logger(custom_log_dir=None):
    """
    Configura o sistema de log da aplicacao.
    
    Args:
        custom_log_dir (Path, optional): Diretorio onde os logs serao salvos.
    """
    # Evitar importacao circular
    from CloudQuest.utils.paths import APP_PATHS
    
    if log.handlers:
        # Se o logger ja esta configurado, retornar
        return
    
    # Definir o diretorio de logs
    log_dir = custom_log_dir if custom_log_dir else APP_PATHS['LOGS_DIR']
    
    # Converter para Path, caso seja string
    if isinstance(log_dir, str):
        log_dir = Path(log_dir)
    
    # Criar diretorio de logs se nao existir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Definir arquivo de log com timestamp para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"cloudquest_{timestamp}.log"

    # Configuracao do logger
    log.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                       datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    log.addHandler(file_handler)
    
    # Handler para console (opcional, util para debugging)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                         datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    log.addHandler(console_handler)
    
    # Log de inicializacao
    log.debug(f"Logger inicializado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.debug(f"Arquivo de log: {log_file}")
    
    return log