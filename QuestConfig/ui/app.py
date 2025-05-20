# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Aplicacao principal do QuestConfig.
"""

import os
import tkinter as tk
from pathlib import Path

from ..utils.logger import setup_logger, write_log
from ..utils.paths import get_app_paths
from ..services import ServiceFactory
from .views import QuestConfigView


class QuestConfigApp:
    """Aplicacao principal do QuestConfig."""
    
    def __init__(self):
        self.app_paths = get_app_paths()
        self.setup_environment()
        
        # Criar factory para servicos
        self.service_factory = ServiceFactory()
    
    def setup_environment(self) -> None:
        """Configura o ambiente da aplicacao."""
        # Configurar log
        setup_logger(self.app_paths['log_dir'])
        write_log("Iniciando QuestConfig Game Configurator")
    
    def run(self) -> None:
        """Executa a aplicacao."""
        root = tk.Tk()
        root.title("QuestConfig Game Configurator")
        
        # Configurar icone
        try:
            icon_path = self.app_paths['icon_path']
            if Path(icon_path).exists():
                root.iconbitmap(icon_path)
        except Exception as e:
            write_log(f"Erro ao carregar icone: {str(e)}", level='WARNING')
        
        # Inicializar servicos para a interface
        config_service = self.service_factory.create_config_service(self.app_paths)
        steam_service = self.service_factory.create_game_info_service("steam")
        pcgamingwiki_service = self.service_factory.create_game_info_service("pcgamingwiki")
        shortcut_service = self.service_factory.create_shortcut_service(self.app_paths.get('batch_path'))
        
        # Iniciar interface com as dependencias
        view = QuestConfigView(
            root, 
            self.app_paths,
            config_service=config_service,
            steam_service=steam_service,
            pcgamingwiki_service=pcgamingwiki_service,
            shortcut_service=shortcut_service
        )
        
        # Iniciar loop principal
        root.mainloop()


def main():
    """Funcao principal da aplicacao."""
    app = QuestConfigApp()
    app.run()


if __name__ == "__main__":
    main() 