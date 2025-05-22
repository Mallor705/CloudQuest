#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Interface de notificacoes personalizadas.
"""

import os
import sys
import threading
import customtkinter as ctk
from PIL import Image
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
        self.root = ctk.CTk()
        self.root.withdraw()  # Esconde a janela principal
        self.root.title("CloudQuest Notification")
        
        # Configuracoes da janela
        self.root.overrideredirect(True)  # Remove bordas e titulo
        self.root.geometry(f"{NOTIFICATION_WIDTH}x{NOTIFICATION_HEIGHT}")
        self.root.configure(fg_color=self._rgb_to_hex(COLORS["background"]))
        
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
        """Posiciona a janela no canto inferior direito do monitor principal."""
        try:
            # Se estamos no Windows, vamos usar a API Win32 para detectar o monitor principal
            if sys.platform == "win32":
                try:
                    # Tenta importar a biblioteca win32
                    import win32api
                    
                    # Obtém informações do monitor principal (monitor com flags = 1)
                    monitors = win32api.EnumDisplayMonitors()
                    monitor_info = win32api.GetMonitorInfo(monitors[0][0])
                    
                    # Para cada monitor, verifica se é o primário
                    for monitor in monitors:
                        info = win32api.GetMonitorInfo(monitor[0])
                        if info['Flags'] == 1:  # Primary monitor
                            monitor_info = info
                            break
                    
                    # Obtém as coordenadas da área de trabalho (sem a barra de tarefas)
                    work_area = monitor_info['Work']
                    
                    # Calcula a posição no canto inferior direito
                    x_position = work_area[2] - NOTIFICATION_WIDTH - 0
                    y_position = work_area[3] - NOTIFICATION_HEIGHT - 0
                    
                    self.root.geometry(f"+{x_position}+{y_position}")
                    return
                except ImportError:
                    log.warning("Módulo win32api não encontrado. Usando método padrão.")
                except Exception as e:
                    log.warning(f"Erro ao obter monitor primário no Windows: {e}")
            
            # Se estamos no Linux, vamos tentar obter informação do Wayland primeiro, depois X11
            elif sys.platform.startswith('linux'):
                import subprocess
                import re
                import json
                
                # Primeiro, tente obter informações via Wayland
                try:
                    # Verificar se estamos rodando em uma sessão Wayland
                    wayland_session = (
                        os.environ.get('WAYLAND_DISPLAY') or 
                        os.environ.get('XDG_SESSION_TYPE') == 'wayland' or
                        os.environ.get('DESKTOP_SESSION', '').lower().find('wayland') >= 0
                    )
                    
                    if wayland_session:
                        log.debug("Detectada sessão Wayland, tentando obter informações de monitor")
                        
                        # Método 1: Tenta usar wlr-randr para obter informações de monitor (para compositors baseados em wlroots)
                        try:
                            wlr_output = subprocess.check_output(['wlr-randr'], stderr=subprocess.DEVNULL).decode()
                            
                            # Procura por linhas como "HDMI-A-1 2560x1440@59.951000Hz (preferred)"
                            monitors = re.findall(r'(\S+)\s+(\d+)x(\d+)@.+?\s+\(preferred\)', wlr_output)
                            
                            if monitors:
                                display_name, width, height = monitors[0]
                                primary_screen_width = int(width)
                                primary_screen_height = int(height)
                                
                                # Calcular posição
                                x_position = primary_screen_width - NOTIFICATION_WIDTH - 00
                                y_position = primary_screen_height - NOTIFICATION_HEIGHT - 60
                                
                                self.root.geometry(f"+{x_position}+{y_position}")
                                log.debug(f"Posição definida via wlr-randr: {x_position}x{y_position}")
                                return
                        except (subprocess.SubprocessError, FileNotFoundError):
                            log.debug("wlr-randr não encontrado ou falhou")
                        
                        # Método 2: Tenta usar swaymsg para obter informações de monitor (para Sway WM)
                        try:
                            sway_output = subprocess.check_output(['swaymsg', '-t', 'get_outputs'], stderr=subprocess.DEVNULL).decode()
                            
                            # Se conseguiu obter as informações, tenta extrair dimensões do monitor principal
                            if 'focused' in sway_output:
                                outputs = json.loads(sway_output)
                                
                                for output in outputs:
                                    if output.get('focused', False):
                                        rect = output.get('rect', {})
                                        primary_screen_width = rect.get('width', 0)
                                        primary_screen_height = rect.get('height', 0)
                                        x_offset = rect.get('x', 0)
                                        y_offset = rect.get('y', 0)
                                        
                                        # Calcular posição
                                        x_position = x_offset + primary_screen_width - NOTIFICATION_WIDTH - 00
                                        y_position = y_offset + primary_screen_height - NOTIFICATION_HEIGHT - 60
                                        
                                        self.root.geometry(f"+{x_position}+{y_position}")
                                        log.debug(f"Posição definida via swaymsg: {x_position}x{y_position}")
                                        return
                        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
                            log.debug("swaymsg não encontrado ou falhou")
                        
                        # Método 3: Tenta usar hyprctl para obter informações de monitor (para Hyprland)
                        try:
                            hypr_output = subprocess.check_output(['hyprctl', 'monitors', '-j'], stderr=subprocess.DEVNULL).decode()
                            monitors = json.loads(hypr_output)
                            
                            for monitor in monitors:
                                if monitor.get('focused', False):
                                    width = monitor.get('width', 0)
                                    height = monitor.get('height', 0)
                                    x = monitor.get('x', 0)
                                    y = monitor.get('y', 0)
                                    
                                    # Calcular posição
                                    x_position = x + width - NOTIFICATION_WIDTH - 00
                                    y_position = y + height - NOTIFICATION_HEIGHT - 60
                                    
                                    self.root.geometry(f"+{x_position}+{y_position}")
                                    log.debug(f"Posição definida via hyprctl: {x_position}x{y_position}")
                                    return
                        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
                            log.debug("hyprctl não encontrado ou falhou")
                        
                        # Método 4: Para KDE Plasma Wayland
                        try:
                            kscreen_output = subprocess.check_output(['kscreen-doctor', '-j'], stderr=subprocess.DEVNULL).decode()
                            kscreen_data = json.loads(kscreen_output)
                            
                            for output in kscreen_data.get('outputs', []):
                                if output.get('enabled', False):
                                    width = output.get('size', {}).get('width', 0)
                                    height = output.get('size', {}).get('height', 0)
                                    x = output.get('pos', {}).get('x', 0)
                                    y = output.get('pos', {}).get('y', 0)
                                    
                                    # Calcular posição
                                    x_position = x + width - NOTIFICATION_WIDTH - 00
                                    y_position = y + height - NOTIFICATION_HEIGHT - 60
                                    
                                    self.root.geometry(f"+{x_position}+{y_position}")
                                    log.debug(f"Posição definida via kscreen-doctor: {x_position}x{y_position}")
                                    return
                        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
                            log.debug("kscreen-doctor não encontrado ou falhou")
                        
                        # Método 5: Para GNOME Wayland
                        try:
                            gnome_output = subprocess.check_output(['gnome-shell', '--version'], stderr=subprocess.DEVNULL).decode()
                            if 'GNOME Shell' in gnome_output:
                                # Se é GNOME, usamos o método padrão do Tkinter, mas ajustamos para GNOME
                                screen_width = self.root.winfo_screenwidth()
                                screen_height = self.root.winfo_screenheight()
                                
                                x_position = screen_width - NOTIFICATION_WIDTH - 00
                                y_position = screen_height - NOTIFICATION_HEIGHT - 60  # Mais espaço para a barra inferior
                                
                                self.root.geometry(f"+{x_position}+{y_position}")
                                log.debug(f"Posição definida para GNOME Wayland: {x_position}x{y_position}")
                                return
                        except (subprocess.SubprocessError, FileNotFoundError):
                            log.debug("Detecção GNOME falhou")
                            
                        # Se todos os métodos específicos falharam, usar o método Tkinter com ajustes para Wayland
                        screen_width = self.root.winfo_screenwidth()
                        screen_height = self.root.winfo_screenheight()
                        
                        if screen_width > 0 and screen_height > 0:
                            x_position = screen_width - NOTIFICATION_WIDTH - 00
                            y_position = screen_height - NOTIFICATION_HEIGHT - 60
                            
                            self.root.geometry(f"+{x_position}+{y_position}")
                            log.debug(f"Posição definida via Tkinter em Wayland: {x_position}x{y_position}")
                            return
                        
                        log.warning("Não foi possível obter informações do monitor via métodos Wayland")
                except Exception as e:
                    log.warning(f"Erro ao detectar informações de monitor via Wayland: {e}")
                
                # Se Wayland falhou, tenta via X11
                try:
                    # Obtém a string de configuração do Xrandr
                    xrandr_output = subprocess.check_output(['xrandr', '--query']).decode()
                    
                    # Procura pelo monitor marcado como "primary"
                    primary_info = re.search(r'(\d+x\d+\+\d+\+\d+) primary', xrandr_output)
                    
                    if primary_info:
                        geometry = primary_info.group(1)
                        # Formato: 1920x1080+0+0
                        width, rest = geometry.split('x')
                        height, x_offset, y_offset = rest.split('+')
                        
                        primary_screen_width = int(width)
                        primary_screen_height = int(height)
                        x_offset = int(x_offset)
                        y_offset = int(y_offset)
                        
                        # Calcular posição no monitor principal
                        x_position = x_offset + primary_screen_width - NOTIFICATION_WIDTH - 00
                        y_position = y_offset + primary_screen_height - NOTIFICATION_HEIGHT - 60
                        
                        self.root.geometry(f"+{x_position}+{y_position}")
                        return
                except Exception as e:
                    log.warning(f"Não foi possível detectar o monitor primário via xrandr: {e}")
            
            # # Método padrão do Tkinter (fallback)
            # # Isso deve funcionar para a maioria dos casos simples onde o monitor primário é o único ou o primeiro
            # primary_screen_width = self.root.winfo_screenwidth()
            # primary_screen_height = self.root.winfo_screenheight()
            
            # x_position = primary_screen_width - NOTIFICATION_WIDTH - 0
            # y_position = primary_screen_height - NOTIFICATION_HEIGHT - 0
            
        except Exception as e:
            log.warning(f"Erro ao determinar monitor primário: {e}")
            # Fallback absoluto para o comportamento mais simples possível
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x_position = screen_width - NOTIFICATION_WIDTH - 0
            y_position = screen_height - NOTIFICATION_HEIGHT - 0
        
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
            # BASE_DIR aqui se refere ao diretório _MEIPASS onde os assets estão embutidos
            possible_dirs = [
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
        self.frame = ctk.CTkFrame(self.root, fg_color=self._rgb_to_hex(COLORS["background"]), width=NOTIFICATION_WIDTH, height=NOTIFICATION_HEIGHT)
        self.frame.pack(fill="both", expand=True)
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
                icon_photo = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(55, 44))
                
                icon_label = ctk.CTkLabel(self.frame, image=icon_photo, text="", fg_color=self._rgb_to_hex(COLORS["background"]))
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
                bg_photo = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(103, 83))
                
                bg_label = ctk.CTkLabel(self.frame, image=bg_photo, text="", fg_color=self._rgb_to_hex(COLORS["background"]))
                bg_label.image = bg_photo  # Manter referencia
                bg_label.place(x=201, y=-4)
            except Exception as e:
                log.error(f"Erro ao carregar background {bg_path}: {e}")
        else:
            log.warning(f"Nao foi possivel encontrar o background: {bg_name}")
        
        # Adicionar titulo
        title_label = ctk.CTkLabel(
            self.frame, 
            text="CloudQuest",
            font=("Segoe UI", 7, "bold"),
            text_color=self._rgb_to_hex(COLORS["text_secondary"]),
            fg_color=self._rgb_to_hex(COLORS["background"])
        )
        title_label.place(x=75, y=10)
        
        # Adicionar nome do jogo
        game_label = ctk.CTkLabel(
            self.frame, 
            text=game_name,
            font=("Segoe UI", 11, "bold"),
            text_color=self._rgb_to_hex(COLORS["text_primary"]),
            fg_color=self._rgb_to_hex(COLORS["background"])
        )
        game_label.place(x=75, y=27)
        
        # Adicionar mensagem de status
        # Determinar mensagem de status com base no tipo e direcao
        if notification_type == "error":
            status_message = "Falha no download!" if direction == "down" else "Falha no upload!"
            status_color = self._rgb_to_hex(COLORS["error"])
        else:
            status_message = "Atualizando seu progresso..." if direction == "down" else "Sincronizando a nuvem..."
            status_color = self._rgb_to_hex(COLORS["text_secondary"])
        
        status_label = ctk.CTkLabel(
            self.frame, 
            text=status_message,
            font=("Segoe UI", 7),
            text_color=status_color,
            fg_color=self._rgb_to_hex(COLORS["background"])
        )
        status_label.place(x=75, y=45)
    
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