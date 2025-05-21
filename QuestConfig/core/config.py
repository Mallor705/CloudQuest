# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Gerenciador de configuracoes da aplicacao.
"""

import os
import json
import configparser
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import platform # Adicionado para verificar o SO

from ..interfaces.services import ConfigService
from ..utils.logger import setup_logger, write_log


class AppConfigService:
    """Implementacao do servico de configuracao."""
    
    def __init__(self, app_paths: Dict[str, Path]):
        self.app_paths = app_paths
    
    def load_rclone_remotes(self) -> List[str]:
        """Carrega os remotes configurados no Rclone."""
        if platform.system() == "Windows":
            rclone_conf_path_str = os.path.join(os.environ.get('APPDATA', ''), r"rclone\rclone.conf")
        else: # Linux, macOS, etc.
            rclone_conf_path_str = os.path.expanduser("~/.config/rclone/rclone.conf")
            
        rclone_conf_path = Path(rclone_conf_path_str) # Converter para Path para consistência, embora os.path.isfile funcione com str
        remotes = []
        
        if rclone_conf_path.is_file(): # Usar .is_file() de Path
            try:
                config = configparser.ConfigParser()
                config.read(rclone_conf_path)
                remotes = config.sections()
                
                if remotes:
                    write_log(f"Remotes detectados: {', '.join(remotes)}")
                else:
                    write_log("Nenhum remote configurado encontrado", level='WARNING')
            except Exception as e:
                write_log(f"Falha ao ler rclone.conf: {str(e)}", level='ERROR')
        else:
            write_log("Arquivo rclone.conf nao encontrado", level='WARNING')
        
        return remotes
    
    def save_game_config(self, config_data: Dict[str, Any], profiles_dir: Path) -> Optional[Path]:
        """Salva a configuracao do jogo em um arquivo JSON."""
        try:
            # Garantir que o diretorio existe
            profiles_dir.mkdir(parents=True, exist_ok=True)
            
            # Adicionar timestamp
            config_data["LastModified"] = datetime.datetime.now().isoformat()
            
            # Nome do arquivo baseado no nome interno do jogo
            internal_name = config_data.get("internal_name", "unknown_game")
            
            # Salvar arquivo de configuracao
            config_file = profiles_dir / f"{internal_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            write_log(f"Configuracoes salvas em: {config_file}")
            
            # Criar diretorio local se nao existir
            local_dir = Path(config_data.get("save_location", ""))
            if local_dir and not local_dir.exists() and str(local_dir).strip():
                local_dir.mkdir(parents=True, exist_ok=True)
                write_log(f"Diretorio local criado: {local_dir}")
            
            return config_file
        
        except Exception as e:
            write_log(f"Erro ao salvar configuracao: {str(e)}", level='ERROR')
            return None
    
    def load_game_config(self, game_name_internal: str, profiles_dir: Path) -> Optional[Dict[str, Any]]:
        """Carrega a configuracao de um jogo a partir do arquivo JSON."""
        try:
            config_file = profiles_dir / f"{game_name_internal}.json"
            
            if not config_file.exists():
                write_log(f"Arquivo de configuracao nao encontrado: {config_file}", level='WARNING')
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            write_log(f"Configuracao carregada: {game_name_internal}")
            return config_data
        
        except Exception as e:
            write_log(f"Erro ao carregar configuracao: {str(e)}", level='ERROR')
            return None
    
    def get_default_values(self) -> Dict[str, Any]:
        """Retorna valores padrao para os campos do formulario."""
        if platform.system() == "Windows":
            default_rclone_path = os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), r"Rclone\rclone.exe")
        else: # Linux, macOS, etc.
            default_rclone_path = "rclone"
            
        return {
            'rclone_path': default_rclone_path,
            'steam_uid': ''
        } 