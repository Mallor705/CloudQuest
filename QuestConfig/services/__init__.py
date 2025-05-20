#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Factory para servicos.
Fornece metodos para instanciar servicos com as dependencias adequadas.
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
    """Factory para criar instancias de servicos."""
    
    @staticmethod
    def create_config_service(app_paths: Dict[str, Path]) -> ConfigService:
        """Cria uma instancia do servico de configuracao."""
        return AppConfigService(app_paths)
    
    @staticmethod
    def create_game_info_service(service_name: str = "steam") -> GameInfoService:
        """
        Cria uma instancia do servico de informacoes de jogos.
        
        Args:
            service_name: Nome do servico ('steam' ou 'pcgamingwiki')
            
        Returns:
            Servico de informacoes de jogos
        """
        if service_name.lower() == "pcgamingwiki":
            return PCGamingWikiService()
        else:
            return SteamService()
    
    @staticmethod
    def create_save_detector_service(executable_path: Optional[str] = None) -> SaveDetectorService:
        """
        Cria uma instancia do servico detector de saves.
        
        Args:
            executable_path: Caminho para o executavel do jogo
            
        Returns:
            Um objeto SaveDetectorService ou None se nao for possivel criar
        """
        if executable_path:
            return SaveDetectorServiceImpl(executable_path)
        return None
    
    @staticmethod
    def create_shortcut_service(batch_path: Optional[Path] = None) -> ShortcutService:
        """Cria uma instancia do servico de criacao de atalhos."""
        return ShortcutCreatorService(batch_path) 