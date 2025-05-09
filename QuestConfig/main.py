#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QuestConfig - Game Configurator

Interface gráfica para adicionar novos jogos à configuração do CloudQuest.
Coleta informações sobre o jogo, verifica dados na Steam, configura sincronização com Rclone
e cria perfil de configuração com atalho na área de trabalho.

Requisitos:
    Python 3.6 ou superior
    Bibliotecas: requests, tkinter, win32com.client
"""

import os
import sys
import ctypes
import tkinter as tk
from pathlib import Path

# Importação de módulos locais
from utils.gui import QuestConfigGUI
from utils.logger import setup_logger, write_log
from utils.path_utils import get_app_paths

def is_admin():
    """Verifica se o script está sendo executado como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def main():
    """Função principal da aplicação"""
    # Configurar diretórios da aplicação
    app_paths = get_app_paths()
    
    # Configurar log
    setup_logger(app_paths['log_dir'])
    write_log("Iniciando QuestConfig Game Configurator GUI")
    
    # Iniciar interface gráfica
    root = tk.Tk()
    app = QuestConfigGUI(root, app_paths)
    
    # Configurar ícone
    try:
        icon_path = app_paths['icon_path']
        if icon_path.exists():
            root.iconbitmap(icon_path)
    except Exception as e:
        write_log(f"Erro ao carregar ícone: {str(e)}", level='WARNING')
    
    root.mainloop()

if __name__ == "__main__":
    # Verificar se executando com privilégios de administrador se necessário
    if is_admin():
        main()
    else:
        # Re-executa o script com privilégios de administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)