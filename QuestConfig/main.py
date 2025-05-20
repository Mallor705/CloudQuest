#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QuestConfig - Game Configurator

Interface gráfica para adicionar novos jogos à configuração do CloudQuest.
Coleta informações sobre o jogo, verifica dados na Steam, configura sincronização com Rclone
e cria perfil de configuração com atalho na área de trabalho.

Requisitos:
    Python 3.6 ou superior
    Bibliotecas: requests, tkinter, psutil, watchdog, win32com.client
"""

from .ui.app import main

if __name__ == "__main__":
    main()