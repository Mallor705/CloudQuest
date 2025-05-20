"""
Interfaces para os serviços da aplicação.
Define os contratos que as implementações concretas devem seguir.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol
from pathlib import Path


class ConfigService(Protocol):
    """Interface para o serviço de configuração."""
    
    def load_rclone_remotes(self) -> List[str]:
        """Carrega os remotes configurados no Rclone"""
        ...
    
    def save_game_config(self, config_data: Dict[str, Any], profiles_dir: Path) -> Optional[Path]:
        """Salva a configuração do jogo"""
        ...
    
    def load_game_config(self, game_name_internal: str, profiles_dir: Path) -> Optional[Dict[str, Any]]:
        """Carrega a configuração de um jogo"""
        ...
    
    def get_default_values(self) -> Dict[str, Any]:
        """Retorna valores padrão para os campos do formulário"""
        ...


class GameInfoService(Protocol):
    """Interface para o serviço de informações de jogos."""
    
    def detect_appid_from_file(self, executable_path: str) -> Optional[str]:
        """Detecta o AppID do jogo a partir de arquivos no diretório do executável"""
        ...
    
    def fetch_game_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Consulta informações do jogo na API da plataforma"""
        ...
    
    def get_save_location(self, app_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Obtém o local de saves para um jogo"""
        ...


class SaveDetectorService(Protocol):
    """Interface para o serviço de detecção de saves."""
    
    def detect_save_location(self) -> List[str]:
        """Detecta possíveis localizações de saves para um jogo"""
        ...


class ShortcutService(Protocol):
    """Interface para o serviço de criação de atalhos."""
    
    def create_game_shortcut(self, shortcut_data: Dict[str, Any]) -> bool:
        """Cria um atalho para o jogo na área de trabalho"""
        ... 