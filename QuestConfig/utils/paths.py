"""
Utilitários para manipulação de caminhos e arquivos.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Union


def get_app_paths() -> Dict[str, Path]:
    """
    Determina os diretórios da aplicação com base no modo de execução.
    
    Returns:
        dict: Dicionário com os caminhos da aplicação
    """
    if getattr(sys, 'frozen', False):
        # Modo executável
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
        'icon_path': app_root / "assets" / "icons" / "icon.ico",
        'batch_path': app_root / "cloudquest.exe" if (app_root / "cloudquest.exe").exists() else None
    }
    
    # Criar diretórios que não existem
    for path_name in ['log_dir', 'config_dir', 'profiles_dir']:
        paths[path_name].mkdir(parents=True, exist_ok=True)
    
    # Criar diretório de ícones se não existir
    (app_root / "assets" / "icons").mkdir(parents=True, exist_ok=True)
    
    return paths


def validate_path(path: Union[str, Path], path_type: str = 'File') -> bool:
    """
    Valida se um caminho existe e é do tipo correto.
    
    Args:
        path: Caminho a ser validado
        path_type: Tipo de caminho esperado ('File' ou 'Directory')
        
    Returns:
        bool: True se o caminho é válido, False caso contrário
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
    Retorna o caminho para a área de trabalho do usuário.
    
    Returns:
        Path: Caminho para a área de trabalho
    """
    return Path(os.path.join(os.environ['USERPROFILE'], 'Desktop')) 