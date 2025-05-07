# modules/notifications.py
# NOTIFICAÇÕES PERSONALIZADAS
# ====================================================
import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
from pathlib import Path
from .config import write_log

class NotificationWindow:
    """Classe para gerenciar janelas de notificação"""
    
    def __init__(self, title, message, type_="info", direction="sync", game_name=None):
        self.root = tk.Tk()
        self.root.withdraw()  # Esconde a janela principal
        
        # Configurações da janela
        self.window = tk.Toplevel(self.root)
        self.window.title("")
        self.window.overrideredirect(True)  # Remove a borda da janela
        
        # Dimensões e posição
        form_width = 300
        form_height = 75
        self.window.geometry(f"{form_width}x{form_height}")
        
        # Posicionamento na tela
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        right_position = screen_width - 300
        bottom_position = screen_height - 150  # 100px do fundo
        
        if direction == "sync":
            self.window.geometry(f"+{right_position}+{bottom_position}")
        else:
            self.window.geometry(f"+{right_position}+{bottom_position}")
        
        # Propriedades da janela
        self.window.attributes("-topmost", True)
        self.window.configure(bg="#1C2027")
        
        # Frame principal com gradiente
        self.frame = tk.Frame(self.window, bg="#1C2027")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Cria o gradiente visual
        gradient_canvas = tk.Canvas(self.frame, width=form_width, height=form_height, 
                                    bg="#1C2027", highlightthickness=0)
        gradient_canvas.place(x=0, y=0)
        
        # Desenha retângulos com cores gradientes
        for i in range(20):
            # Calcula cores para o gradiente
            r = int(17 + (28-17) * i/20)
            g = int(23 + (32-23) * i/20)
            b = int(30 + (39-30) * i/20)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            y_pos = i * (form_height / 20)
            gradient_canvas.create_rectangle(0, y_pos, form_width, y_pos + (form_height / 20), 
                                            fill=color, outline=color)
        
        # Carrega ícones
        try:
            # Determina o caminho dos ícones
            script_dir = Path(__file__).parent
            assets_path = script_dir.parent / "assets" / "icons"
            
            icon_base_name = "error_" if type_ == "error" else ""
            bg_base_name = "error_" if type_ == "error" else ""
            
            icon_file = f"{icon_base_name}{'down' if direction == 'sync' else 'up'}.png"
            bg_file = f"{bg_base_name}{'down' if direction == 'sync' else 'up'}_background.png"
            
            icon_path = assets_path / icon_file
            bg_path = assets_path / bg_file
            
            if icon_path.exists():
                self.icon_img = Image.open(icon_path)
                self.icon_img = self.icon_img.resize((55, 44), Image.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(self.icon_img)
                
                self.icon_label = tk.Label(self.frame, image=self.icon_photo, bg="#1C2027")
                self.icon_label.place(x=10, y=15)
            else:
                write_log(f"AVISO: Ícone não encontrado: {icon_path}", "Warning")
            
            if bg_path.exists():
                self.bg_img = Image.open(bg_path)
                self.bg_img = self.bg_img.resize((103, 83), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(self.bg_img)
                
                self.bg_label = tk.Label(self.frame, image=self.bg_photo, bg="#1C2027")
                self.bg_label.place(x=201, y=-4)
            else:
                write_log(f"AVISO: Background não encontrado: {bg_path}", "Warning")
        
        except Exception as e:
            write_log(f"Erro ao carregar imagens: {str(e)}", "Error")
        
        # Textos
        self.title_label = tk.Label(self.frame, text="CloudQuest", 
                                   font=("Segoe UI", 7, "bold"),
                                   fg="#8C9197", bg="#1C2027")
        self.title_label.place(x=75, y=15)
        
        self.app_label = tk.Label(self.frame, text=game_name or "Jogo",
                                 font=("Segoe UI", 10, "bold"),
                                 fg="white", bg="#1C2027")
        self.app_label.place(x=75, y=30)
        
        # Define a mensagem de status combinando type_ e direction
        if type_ == "error":
            status_message = "Falha no download!" if direction == "sync" else "Falha no upload!"
            status_color = "#DC3232"  # Vermelho para erros
        else:
            status_message = "Atualizando seu progresso..." if direction == "sync" else "Sincronizando a nuvem..."
            status_color = "#8C9197"  # Cinza para info
        
        self.status_label = tk.Label(self.frame, text=status_message,
                                    font=("Segoe UI", 7, "normal"),
                                    fg=status_color, bg="#1C2027")
        self.status_label.place(x=75, y=52)
        
        # Configura auto-fechamento após alguns segundos
        if type_ != "error":
            self.auto_close_timer = threading.Timer(5.0, self.close)
            self.auto_close_timer.daemon = True
            self.auto_close_timer.start()
    
    def close(self):
        """Fecha a janela de notificação com segurança"""
        try:
            # Verifica se a janela ainda existe antes de fechar
            if self.window.winfo_exists():
                self.window.destroy()
            if self.root.winfo_exists():    
                self.root.destroy()
        except Exception as e:
            write_log(f"Erro ao fechar notificação: {str(e)}", "Error")

def show_custom_notification(title, message, type_="info", direction="sync"):
    """
    Exibe uma notificação personalizada
    :param title: Título da notificação
    :param message: Mensagem da notificação
    :param type_: Tipo de notificação ('info', 'error')
    :param direction: Direção da sincronização ('sync', 'update')
    :return: Objeto de notificação ou None em caso de erro
    """
    
    write_log(f"{title} - {message}", "Error" if type_ == "error" else "Info")
    
    try:
        # Tenta carregar o nome do jogo da configuração
        game_name = None
        try:
            # O módulo de configuração já deve estar carregado
            from . import config
            if hasattr(config, 'config') and config.config and 'game_name' in config.config:
                game_name = config.config['game_name']
        except:
            pass
        
        # Cria a notificação em uma thread separada para não bloquear
        notification = NotificationWindow(title, message, type_, direction, game_name)
        
        # Retorna o objeto de notificação para que possa ser fechado posteriormente
        return notification
    
    except Exception as e:
        write_log(f"ERRO CRÍTICO na notificação: {str(e)}", "Error")
        return None