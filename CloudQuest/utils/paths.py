#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitarios para determinacao de caminhos do sistema.
Este modulo centraliza a logica para determinar os caminhos da aplicacao.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

def get_app_paths() -> Dict[str, Path]:
    """
    Determina os diretorios da aplicacao com base no modo de execucao.
    
    Returns:
        Dict[str, Path]: Dicionario com os caminhos da aplicacao
    """
    if getattr(sys, 'frozen', False):
        # Executando como executavel empacotado (PyInstaller)
        BASE_DIR = Path(sys._MEIPASS)
        APP_DIR = Path(os.path.dirname(sys.executable))
    else:
        # Executando como script Python normal
        BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        APP_DIR = BASE_DIR

    # Diretorios do projeto
    paths = {
        'BASE_DIR': BASE_DIR,
        'APP_DIR': APP_DIR,
        'LOGS_DIR': APP_DIR / "logs",
        'CONFIG_DIR': APP_DIR / "config",
        'PROFILES_DIR': APP_DIR / "config" / "profiles",
        'ASSETS_DIR': APP_DIR / "assets",
        'ICONS_DIR': APP_DIR / "assets" / "icons",
        'TEMP_PROFILE_FILE': Path(os.path.join(tempfile.gettempdir(), "cloudquest_profile.txt"))
    }
    
    # Garantir que diretorios importantes existam
    paths['LOGS_DIR'].mkdir(exist_ok=True, parents=True)
    paths['PROFILES_DIR'].mkdir(exist_ok=True, parents=True)
    paths['ICONS_DIR'].mkdir(exist_ok=True, parents=True)
    
    return paths

# Exportar uma instancia para uso global
APP_PATHS = get_app_paths() 