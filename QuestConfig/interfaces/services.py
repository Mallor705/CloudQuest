# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Interfaces para os servicos da aplicacao.
Define os contratos que as implementacoes concretas devem seguir.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol
from pathlib import Path


class ConfigService(Protocol):
    """Interface para o servico de configuracao."""
    
    def load_rclone_remotes(self) -> List[str]:
        """Carrega os remotes configurados no Rclone"""
        ...
    
    def save_game_config(self, config_data: Dict[str, Any], profiles_dir: Path) -> Optional[Path]:
        """Salva a configuracao do jogo"""
        ...
    
    def load_game_config(self, game_name_internal: str, profiles_dir: Path) -> Optional[Dict[str, Any]]:
        """Carrega a configuracao de um jogo"""
        ...
    
    def get_default_values(self) -> Dict[str, Any]:
        """Retorna valores padrao para os campos do formulario"""
        ...


class GameInfoService(Protocol):
    """Interface para o servico de informacoes de jogos."""
    
    def detect_appid_from_file(self, executable_path: str) -> Optional[str]:
        """Detecta o AppID do jogo a partir de arquivos no diretorio do executavel"""
        ...
    
    def fetch_game_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Consulta informacoes do jogo na API da plataforma"""
        ...
    
    def get_save_location(self, app_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """Obtem o local de saves para um jogo"""
        ...


class SaveDetectorService(Protocol):
    """Interface para o servico de deteccao de saves."""
    
    def detect_save_location(self) -> List[str]:
        """Detecta possiveis localizacoes de saves para um jogo"""
        ...


class ShortcutService(Protocol):
    """Interface para o servico de criacao de atalhos."""
    
    def create_game_shortcut(self, shortcut_data: Dict[str, Any]) -> bool:
        """Cria um atalho para o jogo na area de trabalho"""
        ... 