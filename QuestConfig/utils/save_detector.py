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
        # Lista de arquivos modificados durante a execução
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

        def on_modified(self, event):
            # Adiciona arquivos modificados após 2 segundos do início
            if time.time() - self.detector.start_time > 2:  # Ignora alterações iniciais
                self.detector.modified_files.append(event.src_path)

    def get_common_save_dirs(self):
        """
        Retorna uma lista de diretórios comuns onde saves podem ser armazenados.
        """
        return [
            Path(os.environ['USERPROFILE']) / "Documents",  # Documentos do usuário
            Path(os.environ['APPDATA']),  # Pasta AppData\Roaming
            Path(os.environ['LOCALAPPDATA']),  # Pasta AppData\Local
            self.executable_path.parent  # Pasta do executável
        ]

    def detect_save_location(self):
        """
        Detecta automaticamente o diretório de save executando o jogo e monitorando alterações em arquivos.
        """
        try:
            self.start_time = time.time()
            save_dirs = self.get_common_save_dirs()

            # Configurar monitoramento dos diretórios de save
            event_handler = self.ChangeHandler(self)
            self.observer = Observer()
            for directory in save_dirs:
                if directory.exists():
                    self.observer.schedule(event_handler, str(directory), recursive=True)

            self.observer.start()

            # Executar o jogo
            write_log(f"Iniciando jogo para detecção de saves: {self.executable_path}")
            process = subprocess.Popen([str(self.executable_path)])
            process.wait(timeout=300)  # Timeout de 5 minutos

            time.sleep(5)  # Espera para capturar alterações pós-fechamento
            self.observer.stop()
            self.observer.join()

            # Analisar arquivos modificados
            save_candidates = []
            for f in self.modified_files:
                path = Path(f)
                # Considera apenas arquivos com extensões comuns de save
                if path.suffix.lower() in ('.sav', '.cfg', '.ini', '.dat'):
                    save_candidates.append(path.parent)

            # Encontrar o diretório mais comum entre os candidatos
            if save_candidates:
                return max(set(save_candidates), key=save_candidates.count)
            
            return None

        except Exception as e:
            # Registra erro caso ocorra alguma exceção
            write_log(f"Erro na detecção de saves: {str(e)}", level='ERROR')
            return None