#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudQuest - Aplicativo unificado para sincronizacao e configuracao de saves de jogos
Este e o ponto de entrada principal do aplicativo
"""

import os
import sys
import importlib.util
from pathlib import Path

# Determinar corretamente o diretorio base da aplicacao
if getattr(sys, 'frozen', False):
    # Executando como executavel empacotado (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Executando como script Python normal
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = BASE_DIR

# Adicionar diretorios ao path para garantir que as importacoes funcionem
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Funcao para verificar se um modulo pode ser importado
def check_module(module_name):
    """
    Verifica se um modulo pode ser importado.
    
    Args:
        module_name (str): Nome do modulo a verificar
        
    Returns:
        bool: True se o modulo pode ser importado, False caso contrario
    """
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

# Iniciar a aplicacao principal
if __name__ == "__main__":
    try:
        # Verificar se conseguimos importar os modulos necessarios
        if not check_module("CloudQuest.main"):
            print("Modulo CloudQuest.main nao encontrado. Verificando se precisamos ajustar o PYTHONPATH...")
            
            # Se estamos em um ambiente de desenvolvimento, verificar se o diretorio CloudQuest existe
            if (BASE_DIR / "CloudQuest").is_dir():
                print("Diretorio CloudQuest encontrado, adicionando base ao path...")
            else:
                print(f"ERRO: Diretorio CloudQuest nao encontrado em {BASE_DIR}")
                sys.exit(1)
        
        # Tentar importar o modulo princial
        from CloudQuest.main import main
        print("Import bem-sucedido, iniciando aplicacao...")
        main()
        
    except ImportError as e:
        print(f"Erro ao importar modulos: {e}")
        print("Verifique se os diretorios CloudQuest e QuestConfig estao no PYTHONPATH.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Erro ao iniciar aplicacao: {e}")
        sys.exit(1) 