"""
Gerenciador de configurações da aplicação.
"""

import os
import json
import configparser
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..interfaces.services import ConfigService
from ..utils.logger import setup_logger, write_log


class AppConfigService:
    """Implementação do serviço de configuração."""
    
    def __init__(self, app_paths: Dict[str, Path]):
        self.app_paths = app_paths
    
    def load_rclone_remotes(self) -> List[str]:
        """Carrega os remotes configurados no Rclone."""
        rclone_conf_path = os.path.join(os.environ.get('APPDATA', ''), r"rclone\rclone.conf")
        remotes = []
        
        if os.path.isfile(rclone_conf_path):
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
            write_log("Arquivo rclone.conf não encontrado", level='WARNING')
        
        return remotes
    
    def save_game_config(self, config_data: Dict[str, Any], profiles_dir: Path) -> Optional[Path]:
        """Salva a configuração do jogo em um arquivo JSON."""
        try:
            # Garantir que o diretório existe
            profiles_dir.mkdir(parents=True, exist_ok=True)
            
            # Adicionar timestamp
            config_data["LastModified"] = datetime.datetime.now().isoformat()
            
            # Nome do arquivo baseado no nome interno do jogo
            internal_name = config_data.get("internal_name", "unknown_game")
            
            # Salvar arquivo de configuração
            config_file = profiles_dir / f"{internal_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            write_log(f"Configurações salvas em: {config_file}")
            
            # Criar diretório local se não existir
            local_dir = Path(config_data.get("save_location", ""))
            if local_dir and not local_dir.exists() and str(local_dir).strip():
                local_dir.mkdir(parents=True, exist_ok=True)
                write_log(f"Diretório local criado: {local_dir}")
            
            return config_file
        
        except Exception as e:
            write_log(f"Erro ao salvar configuração: {str(e)}", level='ERROR')
            return None
    
    def load_game_config(self, game_name_internal: str, profiles_dir: Path) -> Optional[Dict[str, Any]]:
        """Carrega a configuração de um jogo a partir do arquivo JSON."""
        try:
            config_file = profiles_dir / f"{game_name_internal}.json"
            
            if not config_file.exists():
                write_log(f"Arquivo de configuração não encontrado: {config_file}", level='WARNING')
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            write_log(f"Configuração carregada: {game_name_internal}")
            return config_data
        
        except Exception as e:
            write_log(f"Erro ao carregar configuração: {str(e)}", level='ERROR')
            return None
    
    def get_default_values(self) -> Dict[str, Any]:
        """Retorna valores padrão para os campos do formulário."""
        return {
            'rclone_path': os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), r"Rclone\rclone.exe"),
            'steam_uid': ''
        } 