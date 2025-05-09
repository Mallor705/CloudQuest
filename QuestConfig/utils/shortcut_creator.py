#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para criação de atalhos no Windows.
Fornece funções para criar atalhos na área de trabalho.
"""

import os
import win32com.client
import re
from pathlib import Path

from .logger import write_log
from .path_utils import validate_path, get_desktop_path    

def create_game_shortcut(game_config, bat_path):
    """
    Cria um atalho para o jogo na área de trabalho
    
    Args:
        game_config (dict): Configuração do jogo
        bat_path (Path): Caminho para o script batch que lança o jogo
    
    Returns:
        bool: True se o atalho foi criado com sucesso, False caso contrário
    """
    try:
        # Obter informações necessárias
        game_name = game_config.get("GameName", "Jogo Desconhecido")
        game_name_internal = game_config.get("InternalName", "unknown_game")
        executable_path = game_config.get("ExecutablePath", "")
        
        # Sanitiza o nome do jogo para remover caracteres inválidos
        safe_name = re.sub(r'[<>:"/\\|?*]', '', game_name)  # Remove caracteres proibidos

        # Caminho para a área de trabalho
        desktop_path = get_desktop_path()
        shortcut_path = desktop_path / f"{safe_name}.lnk"

        if validate_path(bat_path, 'File'):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(shortcut_path))
            shortcut.TargetPath = 'cmd.exe'
            shortcut.Arguments = f'/c "{bat_path}" "{game_name_internal}"'
            shortcut.WorkingDirectory = str(Path(executable_path).parent)
            
            # Definir ícone do jogo
            if validate_path(executable_path, 'File'):
                shortcut.IconLocation = f"{executable_path},0"
            
            shortcut.Save()
            
            write_log(f"Atalho criado: {shortcut_path}")
            return True
        else:
            write_log(f"Arquivo de script não encontrado: {bat_path}", level='WARNING')
            return False
    except Exception as e:
        write_log(f"Erro ao criar atalho: {str(e)}", level='ERROR')
        return False