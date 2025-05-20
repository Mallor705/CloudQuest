#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de logging para a aplicacao.
"""

import os
import logging
import datetime
from pathlib import Path
from typing import Optional


# Configuracao global
LOGGER = None
LOG_FILE = None


def setup_logger(log_dir: Path, level: str = 'INFO') -> None:
    """
    Configura o sistema de log.
    
    Args:
        log_dir: Diretorio para salvar os logs
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global LOGGER, LOG_FILE
    
    # Criar diretorio de logs se nao existir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Criar nome do arquivo com data
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"questconfig_{date_str}.log"
    LOG_FILE = log_file
    
    # Configurar logger
    LOGGER = logging.getLogger('questconfig')
    LOGGER.setLevel(getattr(logging, level))
    
    # Adicionar handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                       datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    LOGGER.addHandler(file_handler)
    
    # Adicionar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    LOGGER.addHandler(console_handler)
    
    # Log inicial
    LOGGER.info(f"Iniciando sessao de log: {log_file}")
    LOGGER.info(f"Versao QuestConfig: 1.0.0")


def write_log(message: str, level: str = 'INFO') -> None:
    """
    Escreve uma mensagem no log.
    
    Args:
        message: Mensagem a ser registrada
        level: Nivel do log (INFO, WARNING, ERROR, CRITICAL, DEBUG)
    """
    global LOGGER
    
    if LOGGER is None:
        # Configuracao padrao se nao inicializado
        setup_logger(Path.cwd() / "logs")
    
    log_method = getattr(LOGGER, level.lower(), LOGGER.info)
    log_method(message)


def get_log_file() -> Optional[Path]:
    """
    Retorna o caminho do arquivo de log atual.
    
    Returns:
        Path: Caminho do arquivo de log ou None
    """
    global LOG_FILE
    return LOG_FILE


def get_timestamped_message(message: str) -> str:
    """
    Adiciona timestamp a mensagem.
    
    Args:
        message: Mensagem original
        
    Returns:
        str: Mensagem com timestamp
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {message}"