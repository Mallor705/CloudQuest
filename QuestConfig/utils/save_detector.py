#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para detecção automática de locais de save.
"""

import os  # Importa funcionalidades do sistema operacional
import time  # Importa funções relacionadas a tempo
import subprocess  # Permite executar processos externos
from pathlib import Path  # Facilita manipulação de caminhos
from watchdog.observers import Observer  # Observa mudanças no sistema de arquivos
from watchdog.events import FileSystemEventHandler  # Manipula eventos de arquivos
from .logger import write_log  # Função para registrar logs

class SaveGameDetector:
    """
    Classe responsável por detectar automaticamente o diretório de save de um jogo.
    """
    def __init__(self, executable_path):
        # Caminho do executável do jogo
        self.executable_path = Path(executable_path)
        # Lista de caminhos detectados
        self.detected_paths = []
        # Lista de arquivos modificados
        self.modified_files = []
        # Observador de eventos do sistema de arquivos
        self.observer = None
        # Momento de início da detecção
        self.start_time = None

    class ChangeHandler(FileSystemEventHandler):
        """
        Manipulador de eventos para detectar modificações em arquivos.
        """
        def __init__(self, detector):
            # Referência ao detector principal
            self.detector = detector
            self.ignored_events = 2  # Ignorar eventos iniciais

        def on_any_event(self, event):
            if time.time() - self.detector.start_time < 2:
                return

            path = Path(event.src_path)
            # Registrar apenas pastas e arquivos de save relevantes
            if path.is_dir() or path.suffix.lower() in ('.sav', '.cfg', '.ini', '.dat'):
                self.detector.detected_paths.append(path.parent)  # Registrar o diretório pa

    def get_common_save_dirs(self):
        """
        Retorna uma lista de diretórios comuns onde saves podem ser armazenados.
        """
        return [
            Path(os.environ['USERPROFILE']) / "Documents",  # Documentos do usuário
            Path(os.environ['USERPROFILE']) / "Saved Games",  # Jogos Salvos
            Path(os.environ['APPDATA']),  # Pasta AppData\Roaming
            Path(os.environ['LOCALAPPDATA']),  # Pasta AppData\Local
            self.executable_path.parent  # Pasta do executável
        ]

    def analyze_results(self):
            from collections import defaultdict
            
            # Contar ocorrências de caminhos
            path_counts = defaultdict(int)
            for path in self.detected_paths:
                path_counts[str(path.resolve())] += 1

            # Priorizar pastas que foram criadas/modificadas
            sorted_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Procurar padrões comuns
            for path_str, _ in sorted_paths:
                path = Path(path_str)
                if any(keyword in path_str.lower() for keyword in ['save', 'game', 'data']):
                    return path
                if path.name.lower() == self.executable_path.stem.lower():
                    return path

            return Path(sorted_paths[0][0]) if sorted_paths else None

    def detect_save_location(self):
        """
        Detecta automaticamente o diretório de save executando o jogo e monitorando alterações em arquivos e pastas.
        """
        try:
            self.start_time = time.time()
            save_dirs = self.get_common_save_dirs()

            # Configurar monitoramento dos diretórios de save
            event_handler = self.ChangeHandler(self)
            self.observer = Observer()
            
            for directory in save_dirs:
                if directory.exists():
                    # Monitorar recursivamente com timeout de 30 segundos
                    self.observer.schedule(
                        event_handler,
                        str(directory),
                        recursive=True
                    )

            self.observer.start()

            # Executar o jogo
            write_log(f"Iniciando jogo para detecção de saves: {self.executable_path}")
            process = subprocess.Popen([str(self.executable_path)])
            
            # Tempo máximo de execução: 3 minutos
            for _ in range(180):
                if process.poll() is not None:
                    break
                time.sleep(1)
            else:
                process.kill()

            time.sleep(2)  # Espera final para eventos pendentes
            self.observer.stop()
            self.observer.join()
            
            return self.analyze_results()

        except Exception as e:
            # Registra erro caso ocorra alguma exceção
            write_log(f"Erro na detecção de saves: {str(e)}", level='ERROR')
            return None