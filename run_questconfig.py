#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de execução do QuestConfig
Este arquivo deve ser executado do diretório raiz do projeto
"""

import sys
import os

# Adicionar o diretório do projeto ao caminho de importação
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from QuestConfig.ui.app import main

if __name__ == "__main__":
    main() 