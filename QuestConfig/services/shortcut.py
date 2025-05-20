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
            
            if not game_name or not game_name_internal or not self.batch_path:
                write_log("Dados insuficientes para criar atalho", level='ERROR')
                return False
            
            # Obter caminho da area de trabalho
            desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
            shortcut_path = desktop_path / f"{game_name}.lnk"
            
            # Criar atalho
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = self.batch_path
            shortcut.Arguments = f'game="{game_name_internal}"'
            shortcut.WorkingDirectory = os.path.dirname(self.batch_path)
            
            # Definir icone se disponivel
            icon_path = shortcut_data.get('icon_path', '')
            if icon_path and os.path.isfile(icon_path):
                shortcut.IconLocation = icon_path
            
            # Salvar atalho
            shortcut.save()
            
            write_log(f"Atalho criado em: {shortcut_path}")
            return True
            
        except Exception as e:
            write_log(f"Erro ao criar atalho: {str(e)}", level='ERROR')
            return False 