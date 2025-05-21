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
    batch_executable_name: Union[str, None] = None
    if sys.platform == "win32":
        batch_executable_name = "cloudquest.exe"
    elif sys.platform.startswith("linux"):
        batch_executable_name = "cloudquest.sh"
    # Adicione outras plataformas como macOS aqui se necessário
    # elif sys.platform == "darwin":
    #     batch_executable_name = "cloudquest_launcher.app" # ou .sh

    try:
        from CloudQuest.utils.paths import APP_PATHS as CLOUDQUEST_PATHS
        
        app_dir_for_batch = CLOUDQUEST_PATHS['APP_DIR']
        paths = {
            'app_root': CLOUDQUEST_PATHS['APP_DIR'],
            'script_dir': CLOUDQUEST_PATHS['BASE_DIR'],
            'log_dir': CLOUDQUEST_PATHS['LOGS_DIR'],
            'config_dir': CLOUDQUEST_PATHS['CONFIG_DIR'],
            'profiles_dir': CLOUDQUEST_PATHS['PROFILES_DIR'],
            'assets_dir': CLOUDQUEST_PATHS['ASSETS_DIR'],
            'icon_path': CLOUDQUEST_PATHS['ICONS_DIR'] / "app_icon.ico", # Pode precisar de ajuste para Linux (ex: .png)
        }
    except ImportError:
        if getattr(sys, 'frozen', False):
            script_dir = Path(sys._MEIPASS)
            app_root = Path(sys.executable).parent
        else:
            script_dir = Path(__file__).resolve().parent.parent.parent
            app_root = script_dir
        
        app_dir_for_batch = app_root
        paths = {
            'app_root': app_root,
            'script_dir': script_dir,
            'log_dir': app_root / "logs",
            'config_dir': app_root / "config",
            'profiles_dir': app_root / "config" / "profiles",
            'assets_dir': app_root / "assets",
            # Considerar um ícone .png ou .svg para Linux/outros SO
            'icon_path': app_root / "assets" / "icons" / ("app_icon.png" if sys.platform.startswith("linux") else "app_icon.ico"),
        }
        
        for path_name in ['log_dir', 'config_dir', 'profiles_dir']:
            paths[path_name].mkdir(parents=True, exist_ok=True)
        
        (app_root / "assets" / "icons").mkdir(parents=True, exist_ok=True)

    # Definir batch_path com base no SO e existência do arquivo
    if batch_executable_name:
        candidate_batch_path = app_dir_for_batch / batch_executable_name
        if candidate_batch_path.exists() and candidate_batch_path.is_file():
            paths['batch_path'] = candidate_batch_path
        else:
            paths['batch_path'] = None # Ou um caminho padrão, ou logar um aviso
            # Considerar logar aqui se o batch_executable_name esperado não for encontrado.
    else:
        paths['batch_path'] = None # Plataforma não suportada para batch_path ou nome não definido

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
            # Corrigir a lógica para obter o drive corretamente, Path(path).anchor pode ser vazio
            path_anchor = path_obj.anchor
            if path_anchor: # Ex: "C:\\"
                drive = path_anchor.rstrip(os.sep).rstrip(':') # Remove '\\' e depois ':' -> 'C'
                if drive: # Garante que drive não seja uma string vazia
                    # relative_to precisa de um path_obj que seja filho do anchor
                    # Se path_obj for "C:\\Users\\...", path_obj.relative_to("C:\\") funciona.
                    # Se path_obj for apenas "file.txt", isso falhará.
                    # Vamos assumir que o path original é absoluto para esta lógica.
                    if path_obj.is_absolute():
                         virtual_path = virtual_store / drive / path_obj.relative_to(path_anchor)
                         if virtual_path.exists():
                             # Aqui deveríamos talvez retornar virtual_path ou usar ele, não apenas True
                             if path_type == 'File' and virtual_path.is_file(): return True
                             if path_type == 'Directory' and virtual_path.is_dir(): return True
                             # Se o tipo não corresponder, mas existir, a validação original falhará
                             # então não retornamos False precipitadamente aqui.
        except (KeyError, ValueError) as e: # Adicionar 'e' para a variável da exceção
            # write_log(f"Erro ao verificar VirtualStore: {e}", level='DEBUG') # Opcional
            pass
    
    if path_type == 'File':
        return path_obj.is_file() # .exists() é implícito com .is_file()
    
    if path_type == 'Directory':
        return path_obj.is_dir() # .exists() é implícito com .is_dir()
    
    # Se path_type não for 'File' ou 'Directory', ou se for um tipo desconhecido,
    # apenas checar a existência pode ser um fallback, mas a função é mais específica.
    # Por ora, vamos retornar False se o tipo não for tratado, para ser estrito.
    # Ou, se a intenção original era apenas path_obj.exists() como um fallback:
    # return path_obj.exists() 
    return False # Se path_type não for 'File' ou 'Directory'


def get_desktop_path() -> Path:
    """
    Retorna o caminho para a area de trabalho do usuario, de forma mais agnóstica.
    
    Returns:
        Path: Caminho para a area de trabalho
    """
    if sys.platform == "win32":
        desktop_env_vars = ['USERPROFILE', 'HOMEDRIVE', 'HOMEPATH']
        desktop_folder_name = 'Desktop'
        for var in desktop_env_vars:
            base_path_str = os.getenv(var)
            if base_path_str:
                # Para HOMEDRIVE + HOMEPATH
                if var == 'HOMEDRIVE' and os.getenv('HOMEPATH'):
                    base_path_str = base_path_str + os.getenv('HOMEPATH')
                
                desktop_path = Path(base_path_str) / desktop_folder_name
                if desktop_path.is_dir():
                    return desktop_path
        # Fallback se variáveis de ambiente comuns falharem
        return Path.home() / desktop_folder_name

    elif sys.platform.startswith("linux"):
        # Tentar XDG_DESKTOP_DIR primeiro
        xdg_desktop_dir = os.getenv('XDG_DESKTOP_DIR')
        if xdg_desktop_dir and Path(xdg_desktop_dir).is_dir():
            return Path(xdg_desktop_dir)
        # Fallback para ~/Desktop
        return Path.home() / "Desktop"
    
    # Adicionar macOS se necessário
    # elif sys.platform == "darwin":
    #     return Path.home() / "Desktop"
        
    # Fallback genérico se nenhuma plataforma corresponder
    return Path.home() / "Desktop"