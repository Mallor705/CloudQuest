# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Utilitarios para manipulacao de caminhos e arquivos.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Union


def get_app_paths() -> Dict[str, Path]:
    """
    Determina os diretorios da aplicacao com base no modo de execucao.
    
    Returns:
        dict: Dicionario com os caminhos da aplicacao
    """
    # Primeiro, tenta importar os caminhos do CloudQuest
    try:
        from CloudQuest.utils.paths import APP_PATHS as CLOUDQUEST_PATHS
        
        # Reutilizar os mesmos diretorios do CloudQuest
        paths = {
            'app_root': CLOUDQUEST_PATHS['APP_DIR'],
            'script_dir': CLOUDQUEST_PATHS['BASE_DIR'],
            'log_dir': CLOUDQUEST_PATHS['LOGS_DIR'],
            'config_dir': CLOUDQUEST_PATHS['CONFIG_DIR'],
            'profiles_dir': CLOUDQUEST_PATHS['PROFILES_DIR'],
            'assets_dir': CLOUDQUEST_PATHS['ASSETS_DIR'],
            'icon_path': CLOUDQUEST_PATHS['ICONS_DIR'] / "app_icon.ico",
            'batch_path': CLOUDQUEST_PATHS['APP_DIR'] / "cloudquest.exe" 
                          if (CLOUDQUEST_PATHS['APP_DIR'] / "cloudquest.exe").exists() 
                          else None
        }
        
        return paths
    except ImportError:
        # Se falhar, determinar caminhos independentemente
        if getattr(sys, 'frozen', False):
            # Modo executavel
            script_dir = Path(sys._MEIPASS)
            app_root = Path(sys.executable).parent
        else:
            # Modo script normal
            script_dir = Path(__file__).resolve().parent.parent.parent
            app_root = script_dir
        
        paths = {
            'app_root': app_root,
            'script_dir': script_dir,
            'log_dir': app_root / "logs",
            'config_dir': app_root / "config",
            'profiles_dir': app_root / "config" / "profiles",
            'assets_dir': app_root / "assets",
            'icon_path': app_root / "assets" / "icons" / "app_icon.ico",
            'batch_path': app_root / "cloudquest.exe" if (app_root / "cloudquest.exe").exists() else None
        }
        
        # Criar diretorios que nao existem
        for path_name in ['log_dir', 'config_dir', 'profiles_dir']:
            paths[path_name].mkdir(parents=True, exist_ok=True)
        
        # Criar diretorio de icones se nao existir
        (app_root / "assets" / "icons").mkdir(parents=True, exist_ok=True)
        
        return paths


def validate_path(path: Union[str, Path], path_type: str = 'File') -> bool:
    """
    Valida se um caminho existe e e do tipo correto.
    
    Args:
        path: Caminho a ser validado
        path_type: Tipo de caminho esperado ('File' ou 'Directory')
        
    Returns:
        bool: True se o caminho e valido, False caso contrario
    """
    path_obj = Path(path)
    
    # Verificar Virtual Store no Windows
    if os.name == 'nt' and not path_obj.exists():
        try:
            virtual_store = Path(os.environ['LOCALAPPDATA']) / "VirtualStore"
            drive = Path(path).anchor.replace(':', '')
            if drive:
                virtual_path = virtual_store / drive / path_obj.relative_to(Path(path).anchor)
                if virtual_path.exists():
                    return True
        except (KeyError, ValueError):
            pass
    
    if path_type == 'File' and not path_obj.is_file():
        return False
    
    if path_type == 'Directory' and not path_obj.is_dir():
        return False
    
    return path_obj.exists()


def get_desktop_path() -> Path:
    """
    Retorna o caminho para a area de trabalho do usuario.
    
    Returns:
        Path: Caminho para a area de trabalho
    """
    return Path(os.path.join(os.environ['USERPROFILE'], 'Desktop')) 