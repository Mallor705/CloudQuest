#!/usr/bin/env python3
# CloudQuest - Interface de notificações personalizadas

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
from pathlib import Path

from config.settings import COLORS, NOTIFICATION_WIDTH, NOTIFICATION_HEIGHT, ICONS_DIR
from utils.logger import log

class NotificationWindow:
    """Janela de notificação personalizada."""
    
    def __init__(self, title, message, game_name, direction="sync", notification_type="info"):
        """
        Inicializa a janela de notificação.
        
        Args:
            title (str): Título da notificação
            message (str): Mensagem da notificação
            game_name (str): Nome do jogo
            direction (str): Direção da sincronização ('sync' ou 'update')
            notification_type (str): Tipo da notificação ('info' ou 'error')
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Esconde a janela principal
        self.root.title("CloudQuest Notification")
        
        # Configurações da janela
        self.root.overrideredirect(True)  # Remove bordas e título
        self.root.geometry(f"{NOTIFICATION_WIDTH}x{NOTIFICATION_HEIGHT}")
        self.root.configure(bg=self._rgb_to_hex(COLORS["background"]))
        
        # Garantir que a janela fique sempre no topo
        self.root.attributes("-topmost", True)
        
        # Em Windows, configurações adicionais para transparência
        if sys.platform == "win32":
            self.root.attributes("-transparentcolor", "")
            self.root.wm_attributes("-toolwindow", True)
        
        # Posicionamento na tela (canto inferior direito)
        self._position_window()
        
        # Configuração do conteúdo
        self._setup_ui(title, message, game_name, direction, notification_type)
        
        # Mostrar a janela com efeito de fade-in
        self.root.update_idletasks()
        self.root.deiconify()
        self._fade_in()
        
        # Configuração para fechar a janela
        self.closed = False
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # Iniciar loop principal em thread separada
        self.thread = threading.Thread(target=self._start_event_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _rgb_to_hex(self, rgb):
        """Converte RGB para formato hexadecimal."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _position_window(self):
        """Posiciona a janela no canto inferior direito da tela."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x_position = screen_width - NOTIFICATION_WIDTH - 10
        y_position = screen_height - NOTIFICATION_HEIGHT - 40  # 40px acima da barra de tarefas
        
        self.root.geometry(f"+{x_position}+{y_position}")
    
    def _setup_ui(self, title, message, game_name, direction, notification_type):
        """Configura os elementos visuais da notificação."""
        # Frame principal com gradiente
        self.frame = tk.Frame(self.root, bg=self._rgb_to_hex(COLORS["background"]), width=NOTIFICATION_WIDTH, height=NOTIFICATION_HEIGHT)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.pack_propagate(False)  # Impede que o frame se redimensione
        
        # Determinar ícones baseado no tipo e direção
        icon_prefix = "error_" if notification_type == "error" else ""
        icon_name = f"{icon_prefix}{'down' if direction == 'sync' else 'up'}.png"
        bg_name = f"{icon_prefix}{'down' if direction == 'sync' else 'up'}_background.png"
        
        icon_path = ICONS_DIR / icon_name
        bg_path = ICONS_DIR / bg_name
        
        # Verificar se os ícones existem
        if not icon_path.exists():
            log.warning(f"Ícone não encontrado: {icon_path}")
            icon_path = None
        
        if not bg_path.exists():
            log.warning(f"Background não encontrado: {bg_path}")
            bg_path = None
        
        # Adicionar ícone (se existir)
        if icon_path:
            try:
                icon_img = Image.open(icon_path)
                icon_img = icon_img.resize((55, 44), Image.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_img)
                
                icon_label = tk.Label(self.frame, image=icon_photo, bg=self._rgb_to_hex(COLORS["background"]))
                icon_label.image = icon_photo  # Manter referência
                icon_label.place(x=10, y=15)
            except Exception as e:
                log.error(f"Erro ao carregar ícone: {e}")
        
        # Adicionar background (se existir)
        if bg_path:
            try:
                bg_img = Image.open(bg_path)
                bg