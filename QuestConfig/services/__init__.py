"""
Factory para serviços.
Fornece métodos para instanciar serviços com as dependências adequadas.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from ..interfaces.services import ConfigService, GameInfoService, SaveDetectorService, ShortcutService
from ..core.config import AppConfigService
from .steam import SteamService
from .pcgamingwiki import PCGamingWikiService
from .save import SaveDetectorService as SaveDetectorServiceImpl
from .shortcut import ShortcutCreatorService


class ServiceFactory:
    """Factory para criar instâncias de serviços."""
    
    @staticmethod
    def create_config_service(app_paths: Dict[str, Path]) -> ConfigService:
        """Cria uma instância do serviço de configuração."""
        return AppConfigService(app_paths)
    
    @staticmethod
    def create_game_info_service(service_name: str = "steam") -> GameInfoService:
        """
        Cria uma instância do serviço de informações de jogos.
        
        Args:
            service_name: Nome do serviço ('steam' ou 'pcgamingwiki')
            
        Returns:
            Serviço de informações de jogos
        """
        if service_name.lower() == "pcgamingwiki":
            return PCGamingWikiService()
        else:
            return SteamService()
    
    @staticmethod
    def create_save_detector_service(executable_path: Optional[str] = None) -> SaveDetectorService:
        """
        Cria uma instância do serviço detector de saves.
        
        Args:
            executable_path: Caminho para o executável do jogo
            
        Returns:
            Um objeto SaveDetectorService ou None se não for possível criar
        """
        if executable_path:
            return SaveDetectorServiceImpl(executable_path)
        return None
    
    @staticmethod
    def create_shortcut_service(batch_path: Optional[Path] = None) -> ShortcutService:
        """Cria uma instância do serviço de criação de atalhos."""
        return ShortcutCreatorService(batch_path) 