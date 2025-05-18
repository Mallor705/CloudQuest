#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de gerenciamento de logs para QuestConfig.
Fornece funções para configuração e escrita de logs.
"""

import logging
from pathlib import Path
import datetime
from logging.handlers import RotatingFileHandler

# Variável global para armazenar logger
logger = None

def setup_logger(log_dir):
    """
    Configura o sistema de logging
    
    Args:
        log_dir (Path): Diretório para armazenar arquivos de log
    """
    global logger
    
    # Cria o diretório de logs se não existir
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Define o arquivo de log
    log_file = log_dir / "questconfig.log"
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=50_000,  # 50 KB
        mode='a',  # Modo append
        backupCount=5,
        encoding='utf-8'
    )

    # Configuração de logs
    logging.basicConfig(
        handlers=[handler],
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Criar logger global
    logger = logging.getLogger('questconfig')
    
    write_log("Sistema de logs inicializado")

def write_log(message, level='INFO'):
    """
    Escreve mensagem no arquivo de log
    
    Args:
        message (str): Mensagem a ser registrada
        level (str): Nível de log (INFO, WARNING, ERROR)
    """
    global logger
    
    # Se o logger ainda não foi inicializado, não faz nada
    if logger is None:
        return
    
    level_map = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING, 
        'ERROR': logging.ERROR,
        'DEBUG': logging.DEBUG
    }
    
    logger.log(level_map.get(level, logging.INFO), message)

def get_timestamped_message(message):
    """
    Retorna mensagem com timestamp para exibição na interface
    
    Args:
        message (str): Mensagem original
        
    Returns:
        str: Mensagem com timestamp
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {message}"