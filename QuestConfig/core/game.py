"""
Modelo de domínio para Jogos.
Define a entidade Game e suas operações.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class Game:
    """Representa um jogo configurado no sistema."""
    
    # Identificação do jogo
    name: str
    internal_name: str
    app_id: Optional[str] = None
    platform: str = "Steam"  # Steam, GOG, Epic, etc.
    
    # Caminhos e executáveis
    executable_path: Optional[str] = None
    process_name: Optional[str] = None
    
    # Configuração de sincronização
    save_location: Optional[str] = None
    cloud_remote: Optional[str] = None
    cloud_dir: Optional[str] = None
    
    # Metadados
    icon_path: Optional[str] = None
    steam_user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o jogo para um dicionário."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        """Cria um jogo a partir de um dicionário."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def get_save_dir(self) -> Optional[Path]:
        """Retorna o diretório de saves como objeto Path."""
        if not self.save_location:
            return None
        return Path(self.save_location)
    
    def get_executable_dir(self) -> Optional[Path]:
        """Retorna o diretório do executável como objeto Path."""
        if not self.executable_path:
            return None
        return Path(self.executable_path).parent 