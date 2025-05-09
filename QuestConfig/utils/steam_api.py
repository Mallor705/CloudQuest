#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para integração com a API da Steam.
Fornece funções para consulta de informações de jogos.
"""

import re
import requests
from pathlib import Path
from .logger import write_log
from .text_utils import remove_accents

def detect_appid_from_file(executable_path):
    """
    Tenta detectar o AppID do jogo a partir do arquivo steam_appid.txt
    
    Args:
        executable_path (str): Caminho do executável do jogo
    
    Returns:
        str: AppID detectado ou None se não encontrado
    """
    try:
        exe_folder = Path(executable_path).parent
        steam_appid_path = exe_folder / "steam_appid.txt"
        
        if not steam_appid_path.exists():
            write_log(f"Arquivo steam_appid.txt não encontrado", level='WARNING')
            return None
        
        with open(steam_appid_path, 'r') as f:
            raw_content = f.read()
        
        match = re.search(r'\d{4,}', raw_content)
        if match:
            app_id = match.group()
            write_log(f"AppID detectado: {app_id}")
            return app_id
        else:
            write_log("Arquivo steam_appid.txt sem AppID válido", level='WARNING')
            return None
            
    except Exception as e:
        write_log(f"Falha ao ler steam_appid.txt: {str(e)}", level='ERROR')
        return None

def fetch_game_info(app_id):
    """
    Consulta a API da Steam para obter informações do jogo
    
    Args:
        app_id (str): AppID do jogo na Steam
    
    Returns:
        dict: Informações do jogo ou None em caso de erro
    """
    if not re.match(r'^\d+$', app_id):
        write_log(f"AppID inválido: {app_id}", level='WARNING')
        return None
    
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=portuguese"
    
    try:
        write_log(f"Consultando API Steam para AppID: {app_id}")
        headers = {'User-Agent': 'QuestConfig/1.0'}
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
        
        if data[app_id]['success'] and data[app_id]['data']:
            game_name = data[app_id]['data']['name']
            
            # Processa o nome para uso interno
            processed_name = remove_accents(game_name)
            processed_name = re.sub(r'[^\w\s-]', '_', processed_name)
            processed_name = re.sub(r'\s+', '_', processed_name)
            
            result = {
                'name': game_name,
                'internal_name': processed_name,
                'app_id': app_id
            }
            
            write_log(f"Dados obtidos com sucesso para {game_name}")
            return result
        else:
            write_log(f"AppID {app_id} não encontrado ou dados incompletos", level='WARNING')
            return None
            
    except Exception as e:
        write_log(f"Falha na consulta à API Steam: {str(e)}", level='ERROR')
        return None