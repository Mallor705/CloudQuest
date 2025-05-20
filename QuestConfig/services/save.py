# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Servico para deteccao de locais de saves de jogos.
"""

import os
import platform
import time
import subprocess
from pathlib import Path
from typing import List, Optional
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..interfaces.services import SaveDetectorService
from ..utils.logger import write_log


def wait_for_process_end(process_name: str) -> None:
    """Espera o processo terminar."""
    while True:
        found = any(proc.name().lower() == process_name.lower() for proc in psutil.process_iter())
        if not found:
            break
        time.sleep(2)


class SaveDetectorService:
    """Servico de deteccao de saves."""
    
    def __init__(self, executable_path: str):
        self.executable_path = Path(executable_path)
        self.detected_paths = []
        self.observer = None
        self.start_time = None
    
    class ChangeHandler(FileSystemEventHandler):
        def __init__(self, detector):
            self.detector = detector
            
        def on_any_event(self, event):
            if time.time() - self.detector.start_time < 2:
                return

            path = Path(event.src_path).parent
            if path.is_dir():
                self.detector.detected_paths.append(str(path.resolve()))
    
    def get_common_save_dirs(self) -> List[Path]:
        """Retorna diretorios comuns para saves."""
        common_dirs = [
            Path(os.environ['APPDATA']),
            Path(os.environ['LOCALAPPDATA']),
            Path(os.environ['USERPROFILE']) / "Documents",
            Path(os.environ['USERPROFILE']) / "Saved Games",
            Path(os.environ['USERPROFILE']) / "Jogos Salvos",
            self.executable_path.parent,
            # Caminhos especificos da Steam
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / "Steam/userdata",
            Path(os.environ['LOCALAPPDATA']) / "VirtualStore",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / "Steam/steamapps/common",
            # Caminhos para outros clientes
            Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / "Epic Games",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / "GOG Galaxy/Games",
            Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / "EA Games",
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / "Ubisoft/Ubisoft Game Launcher"
        ]
        
        # Adicionar caminhos especificos do Linux via Proton
        if platform.system() == "Linux":
            common_dirs.extend([
                Path.home() / ".steam/steam/steamapps/compatdata",
                Path.home() / ".local/share/Steam/steamapps/compatdata"
            ])
            
        return common_dirs
    
    def filter_system_paths(self, paths: List[str]) -> List[str]:
        """Filtra caminhos do sistema."""
        system_paths = {
            str(Path(os.environ.get('WINDIR', 'C:/Windows'))),
            str(Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))),
            str(Path(os.environ.get('TEMP', 'C:/Temp'))),
            str(Path(os.environ.get('SYSTEMROOT', 'C:/Windows')))
        }
        
        # Diretorios extras a serem ignorados
        ignore_substrings = [
            r"AppData\Local\Temp",
            r"AppData\Roaming\Microsoft",
            r"AppData\Local\Package Cache",
            r"AppData\Local\Packages",
            r"AppData\Local\Microsoft",
            r"AppData\Local\Backup",
            r"AppData\Local\CEF",
            r"AppData\Local\NVIDIA",
            r"AppData\Local\Steam"
        ]
        
        def should_ignore(p: str) -> bool:
            # Ignora se for um dos paths do sistema
            if any(sp in p for sp in system_paths):
                return True
            # Ignora se contiver algum dos substrings especificados
            for sub in ignore_substrings:
                if sub.replace("\\", os.sep) in p:
                    return True
            return False

        return [p for p in paths if not should_ignore(p)]
    
    def detect_save_location(self) -> List[str]:
        """Detecta possiveis localizacoes de saves para um jogo."""
        try:
            self.start_time = time.time()
            self.detected_paths = []
            save_dirs = self.get_common_save_dirs()

            event_handler = self.ChangeHandler(self)
            self.observer = Observer()

            for directory in save_dirs:
                if directory.exists():
                    self.observer.schedule(event_handler, str(directory), recursive=True)

            self.observer.start()

            # Executar o jogo
            write_log(f"Iniciando jogo para deteccao de saves: {self.executable_path}")
            process = subprocess.Popen(
                [str(self.executable_path)],
                cwd=str(self.executable_path.parent)
            )
            
            # Espera o processo do jogo sumir
            wait_for_process_end(self.executable_path.name)

            time.sleep(2)  # Espera final para eventos
            self.observer.stop()
            self.observer.join()

            # Processar resultados
            from collections import defaultdict
            path_counts = defaultdict(int)
            for path in self.detected_paths:
                path_counts[path] += 1

            # Ordenar por frequencia e data de modificacao
            sorted_paths = sorted(
                path_counts.keys(),
                key=lambda x: (-path_counts[x], -Path(x).stat().st_mtime if Path(x).exists() else 0)
            )

            # Filtrar paths do sistema e limitar a 20 resultados
            filtered_paths = self.filter_system_paths(sorted_paths)[:20]

            return filtered_paths

        except Exception as e:
            write_log(f"Erro na deteccao de saves: {str(e)}", level='ERROR')
            return [] 