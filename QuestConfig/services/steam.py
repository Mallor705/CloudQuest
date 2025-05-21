# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Servico de integracao com a API da Steam.
"""

import re
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..interfaces.services import GameInfoService
from ..utils.logger import write_log
from ..utils.text_utils import normalize_game_name
from .pcgamingwiki import PCGamingWikiService


class SteamService:
    """Implementacao do servico de informacoes de jogos da Steam."""
    
    def __init__(self):
        self.pcgaming_wiki = PCGamingWikiService()
    
    def detect_appid_from_file(self, executable_path: str) -> Optional[str]:
        """
        Detecta o AppID do jogo a partir do arquivo steam_appid.txt.
        """
        try:
            exe_folder = Path(executable_path).parent
            steam_appid_files = list(exe_folder.rglob("steam_appid.txt"))
            
            if not steam_appid_files:
                write_log(f"Arquivo steam_appid.txt nao encontrado em {exe_folder} ou subpastas", level='WARNING')
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
                except Exception as e:
                    write_log(f"Falha ao ler {steam_appid_path}: {str(e)}", level='ERROR')
            
            return None
        except Exception as e:
            write_log(f"Falha ao buscar steam_appid.txt: {str(e)}", level='ERROR')
            return None
    
    def fetch_game_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta a API da Steam para obter informacoes do jogo.
        """
        if not re.match(r'^\d+$', app_id):
            write_log(f"AppID invalido: {app_id}", level='WARNING')
            return None
        
        api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=portuguese"
        
        try:
            write_log(f"Consultando API Steam para AppID: {app_id}")
            headers = {'User-Agent': 'QuestConfig/1.0'}
            response = requests.get(api_url, headers=headers, timeout=15)
            data = response.json()
            
            if data[app_id]['success'] and data[app_id]['data']:
                game_name = data[app_id]['data']['name']
                
                # Buscar local de save utilizando o PCGamingWiki
                save_location = self.get_save_location(app_id)
                
                # Processar nome para uso interno
                processed_name = normalize_game_name(game_name)
                
                result = {
                    'name': game_name,
                    'internal_name': processed_name,
                    'app_id': app_id,
                    'save_location': save_location,
                    'platform': 'Steam'
                }
                
                write_log(f"Dados obtidos com sucesso para {game_name}")
                return result
            else:
                write_log(f"AppID {app_id} nao encontrado ou dados incompletos", level='WARNING')
                return None
                
        except Exception as e:
            write_log(f"Falha na consulta a API Steam: {str(e)}", level='ERROR')
            return None
    
    def get_save_location(self, app_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Obtem o local de saves para um jogo usando informacoes da PCGamingWiki.
        """
        try:
            # Tentar obter via PCGamingWiki
            save_info = self.pcgaming_wiki.find_save_locations(app_id, user_id)
            
            # Se encontrou algum caminho existente, retornar
            if save_info and save_info.get("existing_paths"):
                return save_info["existing_paths"][0]
            
            # Se nao encontrou caminho existente mas tem caminhos expandidos, retornar o primeiro
            if save_info and save_info.get("expanded_paths"):
                return save_info["expanded_paths"][0]
            
            # Se não obteve nenhuma informação do PCGamingWiki, tentar caminhos comuns
            if not save_info:
                write_log(f"PCGamingWiki nao retornou locais de save, tentando caminhos comuns", level='INFO')
                
                # Caminhos comuns para saves de jogos Steam
                common_paths = [
                    Path(os.environ['USERPROFILE']) / "Documents" / f"My Games" / f"Steam_{app_id}",
                    Path(os.environ['PROGRAMFILES(X86)']) / "Steam" / "userdata" / 
                        (user_id if user_id else "<userid>") / app_id / "remote",
                    Path(os.environ['APPDATA']) / f"Steam_{app_id}",
                    Path(os.environ['LOCALAPPDATA']) / f"Steam_{app_id}"
                ]
                
                # Verificar se algum caminho existe
                for path in common_paths:
                    if path.exists():
                        write_log(f"Local de save encontrado para AppID {app_id}: {path}")
                        return str(path)
            
            write_log(f"Nenhum local de save encontrado para AppID {app_id}", level='INFO')
            return None
        except Exception as e:
            write_log(f"Erro ao buscar local de save: {str(e)}", level='ERROR')
            return None 