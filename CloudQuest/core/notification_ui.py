#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Interface de notificacoes personalizadas.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
from pathlib import Path

from CloudQuest.config.settings import COLORS, NOTIFICATION_WIDTH, NOTIFICATION_HEIGHT, ICONS_DIR
from CloudQuest.utils.logger import log

# Definir BASE_DIR para usado no _find_icon_path
if getattr(sys, 'frozen', False):
    # Executando como aplicativo compilado
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Executando como script
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent

class NotificationWindow:
    """Janela de notificacao personalizada."""
    
    def __init__(self, title, message, game_name, direction="down", notification_type="info"):
        """
        Inicializa a janela de notificacao.
        
        Args:
            title (str): Titulo da notificacao
            message (str): Mensagem da notificacao
            game_name (str): Nome do jogo
            direction (str): Direcao da sincronizacao ('down' ou 'up')
            notification_type (str): Tipo da notificacao ('info' ou 'error')
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Esconde a janela principal
        self.root.title("CloudQuest Notification")
        
        # Configuracoes da janela
        self.root.overrideredirect(True)  # Remove bordas e titulo
        self.root.geometry(f"{NOTIFICATION_WIDTH}x{NOTIFICATION_HEIGHT}")
        self.root.configure(bg=self._rgb_to_hex(COLORS["background"]))
        
        # Garantir que a janela fique sempre no topo
        self.root.attributes("-topmost", True)
        
        # Em Windows, configuracoes adicionais para transparencia
        if sys.platform == "win32":
            self.root.attributes("-transparentcolor", "")
            self.root.wm_attributes("-toolwindow", True)
        
        # Posicionamento na tela (canto inferior direito)
        self._position_window()
        
        # Configuracao do conteudo
        self._setup_ui(title, message, game_name, direction, notification_type)
        
        # Mostrar a janela com efeito de fade-in
        self.root.update_idletasks()
        self.root.deiconify()
        self._fade_in()
        
        # Configuracao para fechar a janela
        self.closed = False
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # Iniciar loop de eventos de forma assincrona
        self.root.after(100, self._update_loop)  # Novo metodo
    
    def _rgb_to_hex(self, rgb):
        """Converte RGB para formato hexadecimal."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _position_window(self):
        """Posiciona a janela no canto inferior direito da tela."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x_position = screen_width - NOTIFICATION_WIDTH - 00 # 0px de margem
        y_position = screen_height - NOTIFICATION_HEIGHT - 48  # 48px de altura
        
        self.root.geometry(f"+{x_position}+{y_position}")
    
    def _find_icon_path(self, icon_name):
        """
        Localiza um ícone no diretório correto.
        
        Args:
            icon_name (str): Nome do arquivo de ícone
        
        Returns:
            Path: Caminho do arquivo de ícone ou None se não encontrado
        """
        # Caminho da aplicação atual
        if getattr(sys, 'frozen', False):
            # Executando como aplicativo compilado
            base_dir = Path(sys.executable).parent
            
            # Caminhos possíveis em ordem de prioridade (priorizar pasta externa)
            possible_dirs = [
                base_dir / "assets" / "icons",  # Primeira opção: pasta ao lado do EXE
                base_dir / "icons",
                BASE_DIR / "assets" / "icons",
            ]
        else:
            # Executando como script
            possible_dirs = [
                Path("assets") / "icons",
                ICONS_DIR
            ]
        
        # Buscar o arquivo em todos os diretórios possíveis
        for dir_path in possible_dirs:
            icon_path = dir_path / icon_name
            if icon_path.exists():
                log.debug(f"Ícone encontrado: {icon_path}")
                return icon_path
        
        log.warning(f"Ícone não encontrado: {icon_name}")
        return None
    
    def _setup_ui(self, title, message, game_name, direction, notification_type):
        """Configura os elementos visuais da notificacao."""
        # Frame principal com gradiente
        self.frame = tk.Frame(self.root, bg=self._rgb_to_hex(COLORS["background"]), width=NOTIFICATION_WIDTH, height=NOTIFICATION_HEIGHT)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.pack_propagate(False)  # Impede que o frame se redimensione
        
        # Determinar icones baseado no tipo e direcao
        icon_prefix = "error_" if notification_type == "error" else ""
        icon_name = f"{icon_prefix}{'down' if direction == 'down' else 'up'}.png"
        bg_name = f"{icon_prefix}{'down' if direction == 'down' else 'up'}_background.png"
        
        # Buscar caminhos de icones usando o metodo melhorado
        icon_path = self._find_icon_path(icon_name)
        bg_path = self._find_icon_path(bg_name)
        
        # Adicionar icone (se existir)
        if icon_path:
            try:
                icon_img = Image.open(icon_path)
                icon_img = icon_img.resize((55, 44), Image.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_img)
                
                icon_label = tk.Label(self.frame, image=icon_photo, bg=self._rgb_to_hex(COLORS["background"]))
                icon_label.image = icon_photo  # Manter referencia
                icon_label.place(x=10, y=15)
            except Exception as e:
                log.error(f"Erro ao carregar icone {icon_path}: {e}")
        else:
            log.warning(f"Nao foi possivel encontrar o icone: {icon_name}")
        
        # Adicionar background (se existir)
        if bg_path:
            try:
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((103, 83), Image.LANCZOS)
                bg_photo = ImageTk.PhotoImage(bg_img)
                
                bg_label = tk.Label(self.frame, image=bg_photo, bg=self._rgb_to_hex(COLORS["background"]))
                bg_label.image = bg_photo  # Manter referencia
                bg_label.place(x=201, y=-4)
            except Exception as e:
                log.error(f"Erro ao carregar background {bg_path}: {e}")
        else:
            log.warning(f"Nao foi possivel encontrar o background: {bg_name}")
        
        # Adicionar titulo
        title_label = tk.Label(
            self.frame, 
            text="CloudQuest",
            font=("Segoe UI", 7, "bold"),
            fg=self._rgb_to_hex(COLORS["text_secondary"]),
            bg=self._rgb_to_hex(COLORS["background"])
        )
        title_label.place(x=75, y=15)
        
        # Adicionar nome do jogo
        game_label = tk.Label(
            self.frame, 
            text=game_name,
            font=("Segoe UI", 11, "bold"),
            fg=self._rgb_to_hex(COLORS["text_primary"]),
            bg=self._rgb_to_hex(COLORS["background"])
        )
        game_label.place(x=75, y=30)
        
        # Adicionar mensagem de status
        # Determinar mensagem de status com base no tipo e direcao
        if notification_type == "error":
            status_message = "Falha no download!" if direction == "down" else "Falha no upload!"
            status_color = self._rgb_to_hex(COLORS["error"])
        else:
            status_message = "Atualizando seu progresso..." if direction == "down" else "Sincronizando a nuvem..."
            status_color = self._rgb_to_hex(COLORS["text_secondary"])
        
        status_label = tk.Label(
            self.frame, 
            text=status_message,
            font=("Segoe UI", 7),
            fg=status_color,
            bg=self._rgb_to_hex(COLORS["background"])
        )
        status_label.place(x=75, y=52)
    
    def _fade_in(self):
        """Anima a janela com efeito de fade-in."""
        opacity = 0.0
        while opacity < 1.0:
            opacity += 0.1
            self.root.attributes("-alpha", opacity)
            self.root.update()
            time.sleep(0.02)
    
    def _fade_out(self):
        """Anima a janela com efeito de fade-out."""
        opacity = 1.0
        while opacity > 0.0:
            opacity -= 0.1
            self.root.attributes("-alpha", opacity)
            self.root.update()
            time.sleep(0.02)
    
    def _update_loop(self):
        """Atualiza a janela periodicamente sem bloquear a thread principal."""
        try:
            if not self.closed:
                self.root.update()
                self.root.after(100, self._update_loop)  # Reagendar
        except Exception as e:
            log.error(f"Erro no loop de eventos da notificacao: {e}")
    
    def close(self):
        """Fecha a janela de notificacao."""
        if not self.closed:
            try:
                self._fade_out()
                self.root.destroy()
                self.closed = True
            except Exception as e:
                log.error(f"Erro ao fechar notificacao: {e}")
                # Tentar destruir diretamente em caso de erro
                try:
                    self.root.destroy()
                except:
                    pass
                self.closed = True


def show_notification(title, message, game_name, direction="down", notification_type="info"):
    """
    Mostra uma notificacao personalizada ao usuario.
    
    Args:
        title (str): Titulo da notificacao
        message (str): Mensagem da notificacao
        game_name (str): Nome do jogo
        direction (str): Direcao da sincronizacao ('down' para download, 'up' para upload)
        notification_type (str): Tipo da notificacao ('info' ou 'error')
        
    Returns:
        NotificationWindow: Objeto da janela de notificacao ou None em caso de erro
    """
    try:
        notification = NotificationWindow(
            title=title,
            message=message,
            game_name=game_name,
            direction=direction,
            notification_type=notification_type
        )
        return notification
    except Exception as e:
        log.error(f"Erro ao criar notificacao: {e}", exc_info=True)
        return None