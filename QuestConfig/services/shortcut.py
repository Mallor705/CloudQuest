# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Servico para criacao de atalhos na area de trabalho.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from ..interfaces.services import ShortcutService
from ..utils.logger import write_log


class ShortcutCreatorService:
    """Implementacao do servico de criacao de atalhos."""
    
    def __init__(self, batch_path: Optional[str] = None):
        self.batch_path = batch_path
    
    def create_game_shortcut(self, shortcut_data: Dict[str, Any]) -> bool:
        """
        Cria um atalho para o jogo na area de trabalho.
        
        Args:
            shortcut_data: Dicionario com dados do jogo
        
        Returns:
            bool: True se o atalho foi criado com sucesso
        """
        try:
            import win32com.client
            
            game_name = shortcut_data.get('name', '')
            game_name_internal = shortcut_data.get('internal_name', '')
            game_executable = shortcut_data.get('executable_path', '')
            
            if not game_name or not game_name_internal or not self.batch_path:
                write_log("Dados insuficientes para criar atalho", level='ERROR')
                return False
            
            # Obter caminho da area de trabalho
            desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
            shortcut_path = desktop_path / f"{game_name}.lnk"
            
            # Criar atalho
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(self.batch_path) if isinstance(self.batch_path, Path) else self.batch_path
            shortcut.Arguments = f'"{game_name_internal}"'
            
            # Usar o diretório do executável do jogo como "Iniciar em:"
            if game_executable:
                game_exe_path = str(game_executable) if isinstance(game_executable, Path) else game_executable
                working_dir = os.path.dirname(game_exe_path)
                shortcut.WorkingDirectory = working_dir
                write_log(f"Diretório de trabalho definido como: {working_dir}")
            else:
                # Fallback para o diretório do CloudQuest se o executável do jogo não estiver definido
                working_dir = os.path.dirname(str(self.batch_path) if isinstance(self.batch_path, Path) else self.batch_path)
                shortcut.WorkingDirectory = working_dir
                write_log(f"Usando diretório do CloudQuest como fallback: {working_dir}")
            
            # Usar o ícone do executável do jogo
            if game_executable and os.path.isfile(str(game_executable)):
                shortcut.IconLocation = f"{str(game_executable)},0"
                write_log(f"Usando ícone do executável do jogo: {game_executable}")
            else:
                # Fallback para o ícone especificado ou nenhum
                icon_path = shortcut_data.get('icon_path', '')
                if icon_path and os.path.isfile(str(icon_path)):
                    shortcut.IconLocation = str(icon_path)
                    write_log(f"Usando ícone alternativo: {icon_path}")
            
            # Salvar atalho
            shortcut.save()
            
            write_log(f"Atalho criado em: {shortcut_path}")
            return True
            
        except Exception as e:
            write_log(f"Erro ao criar atalho: {str(e)}", level='ERROR')
            return False 