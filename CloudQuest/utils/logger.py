#!/usr/bin/env python3
# CloudQuest - Sistema de logging

import os
import logging
from datetime import datetime
from pathlib import Path

# Configuração global do logger
log = logging.getLogger("CloudQuest")

def setup_logger(log_dir=None):
    """
    Configura o sistema de log da aplicação.
    
    Args:
        log_dir (Path, optional): Diretório onde os logs serão salvos.
    """
    if log.handlers:
        # Se o logger já está configurado, retornar
        return
    
    # Definir o diretório de logs
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    
    # Converter para Path, caso seja string
    if isinstance(log_dir, str):
        log_dir = Path(log_dir)
    
    # Criar diretório de logs se não existir
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Definir arquivo de log com timestamp para evitar conflitos
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"cloudquest_{timestamp}.log"
    
    # Configuração do logger
    log.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
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
    
    # Log de inicialização
    log.debug(f"Logger inicializado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.debug(f"Arquivo de log: {log_file}")