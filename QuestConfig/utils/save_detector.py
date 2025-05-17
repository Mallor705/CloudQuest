#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para detecção de locais de save com interface de seleção manual.
"""

import os
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import defaultdict
from .logger import write_log
import psutil
import time

def wait_for_process_end(process_name):
    while True:
        found = any(proc.name().lower() == process_name.lower() for proc in psutil.process_iter())
        if not found:
            break
        time.sleep(2)
class SaveGameDetector:
    def __init__(self, executable_path):
        self.executable_path = Path(executable_path)
        self.detected_paths = []
        self.observer = None
        self.start_time = None

    class ChangeHandler(FileSystemEventHandler):
        def __init__(self, detector):
            self.detector = detector
            self.ignored_events = 2  # Ignorar eventos iniciais

        def on_any_event(self, event):
            if time.time() - self.detector.start_time < 2:
                return

            path = Path(event.src_path).parent  # Pegar diretório pai
            if path.is_dir():
                self.detector.detected_paths.append(str(path.resolve()))

    def get_common_save_dirs(self):
        return [
            Path(os.environ['APPDATA']),
            Path(os.environ['LOCALAPPDATA']),
            Path(os.environ['USERPROFILE']) / "Documents",
            Path(os.environ['USERPROFILE']) / "Saved Games",
            Path(os.environ['USERPROFILE']) / "Jogos Salvos",
            self.executable_path.parent
        ]

    def filter_system_paths(self, paths):
        system_paths = {
            str(Path(os.environ['WINDIR'])),
            str(Path(os.environ['PROGRAMFILES'])),
            str(Path(os.environ['TEMP'])),
            str(Path(os.environ['SYSTEMROOT']))
        }
        # Diretórios extras a serem ignorados
        ignore_substrings = [
            r"AppData\Local\Temp",
            r"AppData\Roaming\Microsoft",
            r"AppData\Local\Package Cache",
            r"AppData\Local\Packages",
            r"AppData\Local\Microsoft",
            r"AppData\Local\Backup",
            r"AppData\Local\CEF",
            r"AppData\Local\AMD",
            r"AppData\Local\AMD_Common",
            r"AppData\Local\AMDIdentifyWindow",
            r"AppData\Local\ATI",
            r"AppData\Local\Backup",
            r"AppData\Local\NVIDIA",
            r"AppData\Local\NVIDIA Corporation",
            r"AppData\Local\NVIDIA Web Helper",
            r"AppData\Local\Steam",
            r"AppData\Roaming\Code",
            r"AppData\Local\D3DSCache",
            r"AppData\Local\Publisher"
        ]
        def should_ignore(p):
            # Ignora se for um dos paths do sistema
            if any(sp in p for sp in system_paths):
                return True
            # Ignora se contiver algum dos substrings especificados
            for sub in ignore_substrings:
                if sub.replace("\\", os.sep) in p:
                    return True
            return False

        return [p for p in paths if not should_ignore(p)]

    def detect_save_location(self):
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
            write_log(f"Iniciando jogo para detecção de saves: {self.executable_path}")
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
            path_counts = defaultdict(int)
            for path in self.detected_paths:
                path_counts[path] += 1

            # Ordenar por frequência e data de modificação
            sorted_paths = sorted(
                path_counts.keys(),
                key=lambda x: (-path_counts[x], -Path(x).stat().st_mtime)
            )

            # Filtrar paths do sistema e limitar a 20 resultados
            filtered_paths = self.filter_system_paths(sorted_paths)[:20]

            return filtered_paths

        except subprocess.TimeoutExpired:
            write_log("Tempo de execução do jogo excedido", level='WARNING')
            return []
        except Exception as e:
            write_log(f"Erro na detecção de saves: {str(e)}", level='ERROR')
            return []