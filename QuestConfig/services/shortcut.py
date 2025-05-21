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
    
    def _create_windows_shortcut(self, shortcut_data: Dict[str, Any], shortcut_path: Path) -> bool:
        """Cria um atalho para o jogo no Windows."""
        try:
            import win32com.client # type: ignore
            
            game_name_internal = shortcut_data.get('internal_name', '')
            game_executable = shortcut_data.get('executable_path', '')

            if not self.batch_path:
                write_log("Caminho do batch não fornecido para atalho do Windows.", level='ERROR')
                return False

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(self.batch_path) if isinstance(self.batch_path, Path) else self.batch_path
            shortcut.Arguments = f'"{game_name_internal}"'
            
            working_dir_fallback = os.path.dirname(str(self.batch_path) if isinstance(self.batch_path, Path) else self.batch_path)

            if game_executable:
                game_exe_path_str = str(game_executable) if isinstance(game_executable, Path) else game_executable
                working_dir = os.path.dirname(game_exe_path_str)
                shortcut.WorkingDirectory = working_dir
                write_log(f"Diretório de trabalho (Windows) definido como: {working_dir}")
                if os.path.isfile(game_exe_path_str):
                    shortcut.IconLocation = f"{game_exe_path_str},0"
                    write_log(f"Usando ícone do executável do jogo (Windows): {game_exe_path_str}")
            else:
                shortcut.WorkingDirectory = working_dir_fallback
                write_log(f"Usando diretório do CloudQuest como fallback (Windows): {working_dir_fallback}")
            
            if not shortcut.IconLocation:
                icon_path = shortcut_data.get('icon_path', '')
                if icon_path and os.path.isfile(str(icon_path)):
                    shortcut.IconLocation = str(icon_path)
                    write_log(f"Usando ícone alternativo (Windows): {icon_path}")
            
            shortcut.save()
            return True
        except ImportError:
            write_log("A biblioteca pywin32 não está instalada. Atalhos do Windows não podem ser criados.", level='ERROR')
            return False
        except Exception as e:
            write_log(f"Erro ao criar atalho no Windows: {str(e)}", level='ERROR')
            return False

    def _create_linux_shortcut(self, shortcut_data: Dict[str, Any], shortcut_path: Path) -> bool:
        """Cria um arquivo .desktop para o jogo no Linux."""
        try:
            game_name = shortcut_data.get('name', '')
            game_name_internal = shortcut_data.get('internal_name', '')
            game_executable = shortcut_data.get('executable_path', '')
            icon_path_data = shortcut_data.get('icon_path', '')

            if not self.batch_path:
                write_log("Caminho do batch não fornecido para atalho do Linux.", level='ERROR')
                return False

            exec_command = f'"{str(self.batch_path)}" "{game_name_internal}"'
            
            final_working_dir = ""
            if game_executable:
                game_exe_path_str = str(game_executable) if isinstance(game_executable, Path) else game_executable
                final_working_dir = os.path.dirname(game_exe_path_str)
            elif self.batch_path:
                final_working_dir = os.path.dirname(str(self.batch_path) if isinstance(self.batch_path, Path) else self.batch_path)

            desktop_entry_content = [
                "[Desktop Entry]",
                "Version=1.0",
                "Type=Application",
                f"Name={game_name}",
                f"Comment=Atalho para {game_name}",
                f"Exec={exec_command}",
                f"Path={final_working_dir}",
                "Terminal=false",
                "StartupNotify=true"
            ]
            
            final_icon_path = ""
            if game_executable and os.path.isfile(str(game_executable)):
                final_icon_path = str(game_executable)
                write_log(f"Usando ícone do executável do jogo (Linux): {final_icon_path}")
            elif icon_path_data and os.path.isfile(str(icon_path_data)):
                final_icon_path = str(icon_path_data)
                write_log(f"Usando ícone alternativo (Linux): {final_icon_path}")
            
            if final_icon_path:
                desktop_entry_content.append(f"Icon={final_icon_path}")

            with open(shortcut_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(desktop_entry_content) + "\n")
            
            os.chmod(shortcut_path, 0o755)
            return True
        except Exception as e:
            write_log(f"Erro ao criar atalho no Linux: {str(e)}", level='ERROR')
            return False

    def create_game_shortcut(self, shortcut_data: Dict[str, Any]) -> bool:
        """
        Cria um atalho para o jogo na area de trabalho.
        
        Args:
            shortcut_data: Dicionario com dados do jogo
        
        Returns:
            bool: True se o atalho foi criado com sucesso
        """
        game_name = shortcut_data.get('name', '')
        game_name_internal = shortcut_data.get('internal_name', '')
        
        if not game_name or not game_name_internal:
            write_log("Dados insuficientes para criar atalho: nome ou nome interno ausentes.", level='ERROR')
            return False

        if not self.batch_path:
            write_log("Caminho do batch não fornecido para o serviço de criação de atalhos.", level='ERROR')
            return False

        try:
            shortcut_file_path: Optional[Path] = None
            success = False

            if sys.platform == "win32":
                desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
                shortcut_file_path = desktop_path / f"{game_name}.lnk"
                success = self._create_windows_shortcut(shortcut_data, shortcut_file_path)
            elif sys.platform.startswith("linux"):
                desktop_dir_name = os.getenv('XDG_DESKTOP_DIR')
                if desktop_dir_name and Path(desktop_dir_name).is_dir():
                    desktop_path = Path(desktop_dir_name)
                else:
                    desktop_path = Path.home() / "Desktop"

                if not desktop_path.exists() or not desktop_path.is_dir():
                    alt_desktop_path = Path.home() / ".local/share/applications"
                    alt_desktop_path.mkdir(parents=True, exist_ok=True)
                    desktop_path = alt_desktop_path
                    write_log(f"Diretório Desktop não encontrado, usando: {desktop_path}", level='INFO')

                safe_game_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in game_name)
                shortcut_file_path = desktop_path / f"{safe_game_name}.desktop"
                success = self._create_linux_shortcut(shortcut_data, shortcut_file_path)
            else:
                write_log(f"Sistema operacional não suportado para criação de atalhos: {sys.platform}", level='WARNING')
                return False
            
            if success and shortcut_file_path:
                write_log(f"Atalho criado com sucesso em: {shortcut_file_path}")
            elif not success and shortcut_file_path:
                write_log(f"Falha ao criar atalho em: {shortcut_file_path}", level='ERROR')
            elif not success:
                write_log(f"Falha ao criar atalho. Caminho do arquivo de atalho não determinado.", level='ERROR')

            return success
            
        except Exception as e:
            write_log(f"Erro geral ao preparar para criar atalho: {str(e)}", level='ERROR')
            return False 