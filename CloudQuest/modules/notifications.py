# modules/notifications.py
# NOTIFICAÇÕES PERSONALIZADAS - VERSÃO FINAL
# ====================================================
import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
from pathlib import Path
from .config import write_log
import queue

notification_queue = queue.Queue()
active_notifications = {}

# Mantenha uma única instância root
root = tk.Tk()
root.withdraw()

class NotificationWindow:
    """Classe para gerenciar janelas de notificação com controle de tempo"""
    
    def __init__(self, title, message, type_="info", direction="down", game_name=None, notification_id=None):
        self.notification_id = notification_id
        self.root = tk.Tk()
        self.root.withdraw()
        self._closed = False
        
        # Configurações da janela
        self.window = tk.Toplevel(root)
        self.window.title("")
        self.window.overrideredirect(True)
        self.window.notification_id = notification_id
        
        # Dimensões e posição
        form_width = 300
        form_height = 75
        self.window.geometry(f"{form_width}x{form_height}")
        
        # Posicionamento na tela
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        right_position = screen_width - 300
        bottom_position = screen_height - 150
        
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
            r = int(17 + (28-17) * i/20)
            g = int(23 + (32-23) * i/20)
            b = int(30 + (39-30) * i/20)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            y_pos = i * (form_height / 20)
            gradient_canvas.create_rectangle(0, y_pos, form_width, y_pos + (form_height / 20), 
                                            fill=color, outline=color)
        
        # Carrega ícones
        try:
            script_dir = Path(__file__).parent
            assets_path = script_dir.parent / "assets" / "icons"
            
            icon_file = f"{'error_' if type_ == 'error' else ''}{direction}.png"
            bg_file = f"{'error_' if type_ == 'error' else ''}{direction}_background.png"
            
            icon_path = assets_path / icon_file
            bg_path = assets_path / bg_file
            
            if icon_path.exists():
                self.icon_img = Image.open(icon_path)
                self.icon_img = self.icon_img.resize((55, 44), Image.LANCZOS)
                self.icon_photo = ImageTk.PhotoImage(self.icon_img)
                
                self.icon_label = tk.Label(self.frame, image=self.icon_photo, bg="#1C2027")
                self.icon_label.place(x=10, y=15)
            
            if bg_path.exists():
                self.bg_img = Image.open(bg_path)
                self.bg_img = self.bg_img.resize((103, 83), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(self.bg_img)
                
                self.bg_label = tk.Label(self.frame, image=self.bg_photo, bg="#1C2027")
                self.bg_label.place(x=201, y=-4)
        
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
        
        # Mensagem de status
        if type_ == "error":
            status_message = "Falha no download!" if direction == "down" else "Falha no upload!"
            status_color = "#DC3232"
        else:
            status_message = "Sincronizando a nuvem..." if direction == "down" else "Atualizando seu progresso..."
            status_color = "#8C9197"
        
        self.status_label = tk.Label(self.frame, text=status_message,
                                    font=("Segoe UI", 7, "normal"),
                                    fg=status_color, bg="#1C2027")
        self.status_label.place(x=75, y=52)
        
        # Configura timer apenas para notificações de sucesso
        if type_ != "error":
            self.auto_close_timer = threading.Timer(5.0, self.safe_close)
            self.auto_close_timer.daemon = True
            self.auto_close_timer.start()
            active_notifications[notification_id] = self

    def safe_close(self):
        """Fecha a notificação de forma segura"""
        if not self._closed:
            self._closed = True
            try:
                if self.window.winfo_exists():
                    self.window.after(0, self.window.destroy)
                if self.root.winfo_exists():    
                    self.root.after(0, self.root.destroy)
                if self.notification_id in active_notifications:
                    del active_notifications[self.notification_id]
            except Exception as e:
                write_log(f"Erro ao fechar notificação: {str(e)}", "Error")

def _show_notification(title, message, type_, direction, game_name, notification_id):
    """Função interna para criar a notificação na thread principal"""
    try:
        notification = NotificationWindow(
            title=title,
            message=message,
            type_=type_,
            direction=direction,
            game_name=game_name,
            notification_id=notification_id
        )
        return notification
    except Exception as e:
        write_log(f"Erro ao criar notificação: {str(e)}", "Error")
        return None

def show_custom_notification(title, message, type_="info", direction="down"):
    """Cria uma nova notificação com tempo controlado"""
    write_log(f"{title} - {message}", "Error" if type_ == "error" else "Info")
    
    try:
        from .config import config
        game_name = config.get('game_name', None)
    except:
        game_name = None
    
    notification_id = f"{direction}_{time.time()}"
    notification_queue.put(('show', (title, message, type_, direction, game_name, notification_id)))
    return ManagedNotification(notification_id)

class ManagedNotification:
    """Classe wrapper para gerenciar o ciclo de vida da notificação"""
    def __init__(self, notification_id):
        self.notification_id = notification_id
        
    def close(self):
        """Fecha a notificação manualmente"""
        if self.notification_id in active_notifications:
            notification = active_notifications[self.notification_id]
            if hasattr(notification, 'auto_close_timer'):
                notification.auto_close_timer.cancel()
            notification.safe_close()
            notification_queue.put(('force_close', self.notification_id))

def process_notifications():
    """Processa todas as notificações pendentes na fila"""
    while True:
        try:
            cmd, args = notification_queue.get_nowait()
            
            if cmd == 'show':
                title, message, type_, direction, game_name, notification_id = args
                _show_notification(title, message, type_, direction, game_name, notification_id)
                
            elif cmd == 'force_close':
                notification_id = args
                if notification_id in active_notifications:
                    active_notifications[notification_id].safe_close()
                    
            root.update()
            
        except queue.Empty:
            break
        except Exception as e:
            write_log(f"Erro ao processar notificação: {str(e)}", "Error")