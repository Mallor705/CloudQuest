#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para integração com a API da Steam.
Fornece funções para consulta de informações de jogos.
"""

import re
import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from .logger import write_log
from .text_utils import remove_accents
from .steam_savegame_finder import find_save_locations

def detect_appid_from_file(executable_path):
    """
    Tenta detectar o AppID do jogo a partir do arquivo steam_appid.txt
    em todas as pastas e subpastas próximas ao executável.
    
    Args:
        executable_path (str): Caminho do executável do jogo
    
    Returns:
        str: AppID detectado ou None se não encontrado
    """
    try:
        exe_folder = Path(executable_path).parent
        steam_appid_files = list(exe_folder.rglob("steam_appid.txt"))
        
        if not steam_appid_files:
            write_log(f"Arquivo steam_appid.txt não encontrado em {exe_folder} ou subpastas", level='WARNING')
            return None
        
        for steam_appid_path in steam_appid_files:
            try:
                with open(steam_appid_path, 'r') as f:
                    raw_content = f.read()
                
                match = re.search(r'\d{4,}', raw_content)
                if match:
                    app_id = match.group()
                    write_log(f"AppID {app_id} detectado em {steam_appid_path}")
                    return app_id
                else:
                    write_log(f"Arquivo {steam_appid_path} sem AppID válido", level='WARNING')
            except Exception as e:
                write_log(f"Falha ao ler {steam_appid_path}: {str(e)}", level='ERROR')
        
        write_log("Nenhum AppID válido encontrado nos arquivos steam_appid.txt", level='WARNING')
        return None
            
    except Exception as e:
        write_log(f"Falha ao buscar steam_appid.txt: {str(e)}", level='ERROR')
        return None

def get_save_location_for_appid(app_id, steam_uid=None):
    """
    Obtém o local de saves para um jogo usando a API integrada PCGamingWiki
    
    Args:
        app_id (str): Steam AppID do jogo
        steam_uid (str, optional): Steam UserID do jogador

    Returns:
        str: Caminho para o local de saves ou None se não encontrado
    """
    try:
        # Usar o novo módulo para buscar locais de save
        save_info = find_save_locations(app_id, steam_uid)
        
        if save_info and save_info.get("existing_paths"):
            # Se encontrou caminhos que existem, retorna o primeiro
            return save_info["existing_paths"][0]
        elif save_info and save_info.get("expanded_paths"):
            # Se não encontrou caminhos existentes, retorna o primeiro expandido
            return save_info["expanded_paths"][0]
        else:
            write_log(f"Nenhum local de save encontrado para AppID {app_id}", level='WARNING')
            return None
    except Exception as e:
        write_log(f"Erro ao buscar local de save: {str(e)}", level='ERROR')
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
        response = requests.get(api_url, headers=headers, timeout=15)
        data = response.json()
        
        if data[app_id]['success'] and data[app_id]['data']:
            game_name = data[app_id]['data']['name']
            
            # Buscar local de save usando o novo módulo
            save_location = get_save_location_for_appid(app_id)
            
            # Processa o nome para uso interno
            processed_name = remove_accents(game_name)
            processed_name = re.sub(r'[^\w\s-]', '_', processed_name)
            processed_name = re.sub(r'\s+', '_', processed_name)
            
            result = {
                'name': game_name,
                'internal_name': processed_name,
                'app_id': app_id,
                'save_location': save_location
            }
            
            write_log(f"Dados obtidos com sucesso para {game_name}")
            return result
        else:
            write_log(f"AppID {app_id} não encontrado ou dados incompletos", level='WARNING')
            return None
            
    except Exception as e:
        write_log(f"Falha na consulta à API Steam: {str(e)}", level='ERROR')
        return None