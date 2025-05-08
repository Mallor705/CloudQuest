#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudQuest Game Configurator GUI

Interface gráfica para adicionar novos jogos à configuração do CloudQuest.
Coleta informações sobre o jogo, verifica dados na Steam, configura sincronização com Rclone
e cria perfil de configuração com atalho na área de trabalho.

Requisitos:
    Python 3.6 ou superior
    Bibliotecas: requests, unicodedata, re, json, configparser, win32com.client, tkinter
"""

import os
import sys
import re
import json
import logging
import unicodedata
import configparser
import subprocess
import datetime
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import winreg
import win32com.client
import ctypes
import threading

# Configurações iniciais
script_dir = Path(__file__).resolve().parent
cloudquest_root = script_dir.parent
log_dir = cloudquest_root / "logs"
log_file = log_dir / "newgame.log"

# Cria o diretório de logs se não existir
log_dir.mkdir(parents=True, exist_ok=True)

# Configuração de logs
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def write_log(message, level='INFO'):
    """Escrever mensagem no arquivo de log"""
    level_map = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING, 
        'ERROR': logging.ERROR
    }
    logging.log(level_map.get(level, logging.INFO), message)

def validate_path(path, path_type='File'):
    """Valida se um caminho existe e é do tipo correto"""
    path_obj = Path(path)
    
    if not path_obj.exists():
        write_log(f"{path_type} não encontrado: {path}", level='WARNING')
        return False
    
    if path_type == 'File' and not path_obj.is_file():
        write_log(f"O caminho especificado não é um arquivo: {path}", level='WARNING')
        return False
    
    return True

def remove_accents(input_string):
    """Remove acentos de uma string"""
    normalized = unicodedata.normalize('NFKD', input_string)
    return ''.join([c for c in normalized if not unicodedata.combining(c)])

def is_admin():
    """Verifica se o script está sendo executado como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

class CloudQuestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CloudQuest Game Configurator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variáveis para armazenar dados
        self.executable_path = tk.StringVar()
        self.app_id = tk.StringVar()
        self.game_name = tk.StringVar()
        self.game_name_internal = ""
        self.rclone_path = tk.StringVar()
        self.cloud_remote = tk.StringVar()
        self.local_dir = tk.StringVar()
        self.cloud_dir = tk.StringVar()
        self.game_process = tk.StringVar()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        
        # Log widget
        self.log_text = None
        
        # Carregar valores padrões
        self.load_defaults()
        
        # Criar interface
        self.create_widgets()
        
        # Inicializar valores
        self.update_cloud_dir()
        
        write_log("GUI iniciada")
        
    def load_defaults(self):
        """Carrega valores padrões para os campos"""
        # Default Rclone path
        default_rclone_path = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "Rclone\\rclone.exe")
        self.rclone_path.set(default_rclone_path)
        
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        # Estilo
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10))
        self.style.configure('TEntry', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
                
        main_frame = ttk.Frame(self.root, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para organizar as etapas em abas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba 1: Executável e AppID
        tab1 = ttk.Frame(notebook, padding=10)
        notebook.add(tab1, text="1. Executável e AppID")
        
        # Título da seção
        header1 = ttk.Label(tab1, text="Informações do Jogo", style='Header.TLabel')
        header1.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Executável
        ttk.Label(tab1, text="Executável do Jogo:").grid(row=1, column=0, sticky="w", pady=2)
        exe_frame = ttk.Frame(tab1)
        exe_frame.grid(row=1, column=1, sticky="ew", pady=2)
        
        ttk.Entry(exe_frame, textvariable=self.executable_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(exe_frame, text="Procurar...", command=self.browse_executable).pack(side=tk.RIGHT, padx=(5, 0))
        
        # AppID
        ttk.Label(tab1, text="AppID Steam:").grid(row=2, column=0, sticky="w", pady=2)
        appid_frame = ttk.Frame(tab1)
        appid_frame.grid(row=2, column=1, sticky="ew", pady=2)
        
        ttk.Entry(appid_frame, textvariable=self.app_id, width=20).pack(side=tk.LEFT)
        ttk.Button(appid_frame, text="Detectar", command=self.detect_appid).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(appid_frame, text="Consultar Steam", command=self.query_steam_api).pack(side=tk.LEFT, padx=(5, 0))
        
        # Nome do Jogo
        ttk.Label(tab1, text="Nome do Jogo:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(tab1, textvariable=self.game_name, width=50).grid(row=3, column=1, sticky="ew", pady=2)
        
        # Aba 2: Configuração do Rclone
        tab2 = ttk.Frame(notebook, padding=10)
        notebook.add(tab2, text="2. Configuração Rclone")
        
        # Título da seção
        header2 = ttk.Label(tab2, text="Configuração de Sincronização", style='Header.TLabel')
        header2.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Rclone
        ttk.Label(tab2, text="Caminho do Rclone:").grid(row=1, column=0, sticky="w", pady=2)
        rclone_frame = ttk.Frame(tab2)
        rclone_frame.grid(row=1, column=1, sticky="ew", pady=2)
        
        ttk.Entry(rclone_frame, textvariable=self.rclone_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(rclone_frame, text="Procurar...", command=self.browse_rclone).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Remote
        ttk.Label(tab2, text="Cloud Remote:").grid(row=2, column=0, sticky="w", pady=2)
        remote_frame = ttk.Frame(tab2)
        remote_frame.grid(row=2, column=1, sticky="ew", pady=2)
        
        self.remote_combo = ttk.Combobox(remote_frame, textvariable=self.cloud_remote, width=30)
        self.remote_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(remote_frame, text="Detectar Remotes", command=self.detect_remotes).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Local Dir
        ttk.Label(tab2, text="Diretório Local:").grid(row=3, column=0, sticky="w", pady=2)
        local_dir_frame = ttk.Frame(tab2)
        local_dir_frame.grid(row=3, column=1, sticky="ew", pady=2)
        
        ttk.Entry(local_dir_frame, textvariable=self.local_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(local_dir_frame, text="Procurar...", command=self.browse_local_dir).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cloud Dir
        ttk.Label(tab2, text="Diretório na Nuvem:").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(tab2, textvariable=self.cloud_dir, width=50).grid(row=4, column=1, sticky="ew", pady=2)
        
        # Process Name
        ttk.Label(tab2, text="Nome do Processo:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(tab2, textvariable=self.game_process, width=50).grid(row=5, column=1, sticky="ew", pady=2)
        
        # Aba 3: Logs
        tab3 = ttk.Frame(notebook, padding=10)
        notebook.add(tab3, text="3. Logs")
        
        # Área de log
        log_frame = ttk.Frame(tab3)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_label = ttk.Label(log_frame, text="Log de Operações:", style='Header.TLabel')
        log_label.pack(anchor="w", pady=(0, 5))
        
        # Scrollbar para o log
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=20, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Adicionar texto inicial ao log
        self.add_to_log(f"CloudQuest Game Configurator iniciado - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Barra de botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Salvar Configuração", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.root.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Barra de status
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Vincular eventos
        self.executable_path.trace_add("write", self.on_executable_change)
        self.local_dir.trace_add("write", self.update_cloud_dir)
        
    def add_to_log(self, message):
        """Adiciona mensagem ao widget de log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)  # Rola para mostrar a última mensagem
        write_log(message)
    
    def update_status(self, message):
        """Atualiza a barra de status"""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def browse_executable(self):
        """Abre diálogo para selecionar o executável do jogo"""
        filepath = filedialog.askopenfilename(
            title="Selecione o executável do jogo",
            filetypes=[("Executáveis", "*.exe"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.executable_path.set(filepath)
            self.add_to_log(f"Executável selecionado: {filepath}")
    
    def browse_rclone(self):
        """Abre diálogo para selecionar o executável do Rclone"""
        filepath = filedialog.askopenfilename(
            title="Selecione o executável do Rclone",
            filetypes=[("Executáveis", "*.exe"), ("Todos os arquivos", "*.*")]
        )
        if filepath:
            self.rclone_path.set(filepath)
            self.add_to_log(f"Rclone selecionado: {filepath}")
    
    def browse_local_dir(self):
        """Abre diálogo para selecionar o diretório local"""
        directory = filedialog.askdirectory(title="Selecione o diretório local")
        if directory:
            self.local_dir.set(directory)
            self.add_to_log(f"Diretório local selecionado: {directory}")
    
    def on_executable_change(self, *args):
        """Manipula alterações no caminho do executável"""
        exe_path = self.executable_path.get()
        if exe_path and validate_path(exe_path, 'File'):
            # Define o valor padrão para o diretório local
            exe_folder = Path(exe_path).parent
            default_local_dir = os.path.join(os.environ.get('APPDATA', ''), exe_folder.name)
            self.local_dir.set(default_local_dir)
            
            # Define o nome do processo
            process_name = Path(exe_path).stem
            self.game_process.set(process_name)
            
            self.add_to_log(f"Processo detectado: {process_name}")
    
    def update_cloud_dir(self, *args):
        """Atualiza o diretório na nuvem com base no local"""
        local_dir = self.local_dir.get()
        if local_dir:
            cloud_dir_leaf = Path(local_dir).name
            cloud_dir = f"CloudQuest/{cloud_dir_leaf}"
            self.cloud_dir.set(cloud_dir)
    
    def detect_appid(self):
        """Tenta detectar o AppID do jogo a partir do arquivo steam_appid.txt"""
        exe_path = self.executable_path.get()
        if not exe_path:
            messagebox.showwarning("Aviso", "Selecione o executável do jogo primeiro.")
            return
        
        exe_folder = Path(exe_path).parent
        steam_appid_path = exe_folder / "steam_appid.txt"
        
        if validate_path(steam_appid_path, 'File'):
            try:
                with open(steam_appid_path, 'r') as f:
                    raw_content = f.read()
                
                match = re.search(r'\d{4,}', raw_content)
                if match:
                    app_id = match.group()
                    self.app_id.set(app_id)
                    self.add_to_log(f"AppID detectado: {app_id}")
                    return True
                else:
                    self.add_to_log("Arquivo steam_appid.txt sem AppID válido")
                    messagebox.showwarning("Aviso", "Nenhum AppID válido encontrado no arquivo.")
                    return False
            except Exception as e:
                self.add_to_log(f"Falha ao ler steam_appid.txt: {str(e)}")
                messagebox.showerror("Erro", f"Falha ao ler steam_appid.txt: {str(e)}")
                return False
        else:
            self.add_to_log("Arquivo steam_appid.txt não encontrado")
            messagebox.showinfo("Informação", "Arquivo steam_appid.txt não encontrado. Digite o AppID manualmente.")
            return False
    
    def detect_remotes(self):
        """Detecta os remotes configurados no Rclone"""
        rclone_conf_path = os.path.join(os.environ.get('APPDATA', ''), "rclone\\rclone.conf")
        remotes = []
        
        self.update_status("Detectando remotes...")
        
        if validate_path(rclone_conf_path, 'File'):
            try:
                config = configparser.ConfigParser()
                config.read(rclone_conf_path)
                remotes = config.sections()
                
                if remotes:
                    self.remote_combo['values'] = remotes
                    self.add_to_log(f"Remotes detectados: {', '.join(remotes)}")
                    self.update_status(f"{len(remotes)} remote(s) encontrado(s)")
                else:
                    self.add_to_log("Nenhum remote configurado encontrado")
                    self.update_status("Nenhum remote encontrado")
                    messagebox.showwarning("Aviso", "Nenhum remote configurado encontrado no arquivo rclone.conf.")
            except Exception as e:
                self.add_to_log(f"Falha ao ler rclone.conf: {str(e)}")
                self.update_status("Erro ao ler configuração")
                messagebox.showerror("Erro", f"Falha ao ler rclone.conf: {str(e)}")
        else:
            self.add_to_log("Arquivo rclone.conf não encontrado")
            self.update_status("rclone.conf não encontrado")
            messagebox.showwarning("Aviso", "Arquivo rclone.conf não encontrado.")
    
    def query_steam_api(self):
        """Consulta a API Steam para obter informações do jogo"""
        app_id = self.app_id.get()
        
        if not app_id:
            if not self.detect_appid():
                messagebox.showwarning("Aviso", "Por favor, forneça um AppID válido.")
                return
            app_id = self.app_id.get()  # Pega o valor atualizado após a detecção
        
        if not re.match(r'^\d+$', app_id):
            messagebox.showwarning("Aviso", "AppID deve conter apenas números.")
            return
        
        self.update_status("Consultando API Steam...")
        self.add_to_log(f"Consultando API Steam para AppID: {app_id}")
        
        # Executa a consulta em uma thread separada para não bloquear a interface
        threading.Thread(target=self._fetch_steam_data, args=(app_id,), daemon=True).start()
    
    def _fetch_steam_data(self, app_id):
        """Thread worker para buscar dados da Steam API"""
        api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=portuguese"
        
        try:
            headers = {'User-Agent': 'CloudQuest/2.0'}
            response = requests.get(api_url, headers=headers, timeout=10)
            data = response.json()
            
            # Atualiza a UI na thread principal
            self.root.after(0, self._process_steam_response, data, app_id)
        except Exception as e:
            # Atualiza a UI na thread principal em caso de erro
            self.root.after(0, self._handle_steam_error, str(e))
    
    def _process_steam_response(self, data, app_id):
        """Processa a resposta da API Steam e atualiza a UI"""
        try:
            if data[app_id]['success'] and data[app_id]['data']:
                game_name = data[app_id]['data']['name']
                self.game_name.set(game_name)
                self.add_to_log(f"Nome oficial detectado: {game_name}")
                self.update_status("Informações obtidas com sucesso")
                
                # Processar o nome para uso interno
                processed_name = remove_accents(game_name)
                processed_name = re.sub(r'[^\w\s-]', '_', processed_name)
                processed_name = re.sub(r'\s+', '_', processed_name)
                self.game_name_internal = processed_name
                
                messagebox.showinfo("Sucesso", f"Dados obtidos com sucesso!\nJogo: {game_name}")
            else:
                self.add_to_log(f"AppID {app_id} não encontrado ou dados incompletos")
                self.update_status("Falha na consulta")
                messagebox.showwarning("Aviso", f"AppID {app_id} não encontrado ou dados incompletos.")
        except Exception as e:
            self._handle_steam_error(str(e))
    
    def _handle_steam_error(self, error_msg):
        """Trata erros na consulta à API Steam"""
        self.add_to_log(f"Falha na consulta à API Steam: {error_msg}")
        self.update_status("Erro na consulta")
        messagebox.showerror("Erro", f"Falha na consulta à API Steam: {error_msg}")
    
    def save_config(self):
        """Salva as configurações e cria o atalho"""
        # Validar campos obrigatórios
        if not self.validate_fields():
            return
        
        try:
            self.update_status("Salvando configurações...")
            
            # Processa o nome interno do jogo se não foi feito antes
            if not self.game_name_internal:
                game_name_input = self.game_name.get()
                processed_name = remove_accents(game_name_input)
                processed_name = re.sub(r'[^\w\s-]', '_', processed_name)
                processed_name = re.sub(r'\s+', '_', processed_name)
                self.game_name_internal = processed_name
            
            # Prepare config data
            config = {
                "ExecutablePath": self.executable_path.get(),
                "ExeFolder": str(Path(self.executable_path.get()).parent),
                "AppID": self.app_id.get(),
                "GameName": self.game_name.get(),
                "RclonePath": self.rclone_path.get(),
                "CloudRemote": self.cloud_remote.get(),
                "CloudDir": self.cloud_dir.get(),
                "LocalDir": self.local_dir.get(),
                "GameProcess": self.game_process.get(),
                "LastModified": datetime.datetime.now().isoformat()
            }
            
            # Create config directory if it doesn't exist
            config_dir = script_dir.parent / "config/profiles"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save config file
            config_file = config_dir / f"{self.game_name_internal}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.add_to_log(f"Configurações salvas em: {config_file}")
            
            # Create local directory if it doesn't exist
            local_dir_path = Path(self.local_dir.get())
            if not local_dir_path.exists():
                local_dir_path.mkdir(parents=True, exist_ok=True)
                self.add_to_log(f"Diretório local criado: {local_dir_path}")
            
            # Create shortcut
            self.create_shortcut()
            
            self.update_status("Configuração concluída")
            messagebox.showinfo("Sucesso", "Configuração salva com sucesso!")
            
        except Exception as e:
            self.add_to_log(f"Erro ao salvar configuração: {str(e)}")
            self.update_status("Erro ao salvar")
            messagebox.showerror("Erro", f"Falha ao salvar configuração: {str(e)}")
    
    def validate_fields(self):
        """Valida os campos obrigatórios antes de salvar"""
        missing_fields = []
        
        if not self.executable_path.get():
            missing_fields.append("Executável do jogo")
        elif not validate_path(self.executable_path.get(), 'File'):
            messagebox.showerror("Erro", "O executável do jogo não existe.")
            return False
        
        if not self.app_id.get():
            missing_fields.append("AppID Steam")
        
        if not self.game_name.get():
            missing_fields.append("Nome do jogo")
        
        if not self.rclone_path.get():
            missing_fields.append("Caminho do Rclone")
        elif not validate_path(self.rclone_path.get(), 'File'):
            messagebox.showerror("Erro", "O executável do Rclone não existe.")
            return False
        
        if not self.cloud_remote.get():
            missing_fields.append("Cloud Remote")
        
        if not self.local_dir.get():
            missing_fields.append("Diretório local")
        
        if not self.cloud_dir.get():
            missing_fields.append("Diretório na nuvem")
        
        if not self.game_process.get():
            missing_fields.append("Nome do processo")
        
        if missing_fields:
            messagebox.showwarning("Campos obrigatórios", 
                                 "Os seguintes campos são obrigatórios:\n" + 
                                 "\n".join([f"• {field}" for field in missing_fields]))
            return False
        
        return True
    
    def create_shortcut(self):
        """Cria um atalho para o jogo na área de trabalho"""
        try:
            desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
            shortcut_path = desktop_path / f"{self.game_name.get()}.lnk"
            bat_path = script_dir / "cloudquest.bat"
            
            if validate_path(bat_path, 'File'):
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(str(shortcut_path))
                shortcut.TargetPath = 'cmd.exe'
                shortcut.Arguments = f'/c "{bat_path}" "{self.game_name_internal}"'
                shortcut.WorkingDirectory = str(Path(self.executable_path.get()).parent)
                shortcut.IconLocation = f"{self.executable_path.get()},0"
                shortcut.Save()
                
                self.add_to_log(f"Atalho criado: {shortcut_path}")
                return True
            else:
                self.add_to_log(f"Arquivo cloudquest.bat não encontrado em: {bat_path}")
                messagebox.showwarning("Aviso", "Arquivo cloudquest.bat não encontrado!")
                return False
        except Exception as e:
            self.add_to_log(f"Erro ao criar atalho: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao criar atalho: {str(e)}")
            return False

def main():
    write_log("Iniciando CloudQuest Game Configurator GUI")
    
    root = tk.Tk()
    app = CloudQuestGUI(root)
    
    # Configurar ícone (opcional)
    try:
        icon_path = script_dir / "icon.ico"
        if validate_path(icon_path, 'File'):
            root.iconbitmap(icon_path)
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    # Verificar se executando com privilégios de administrador se necessário
    if is_admin():
        main()
    else:
        # Re-executa o script com privilégios de administrador
        write_log("Solicitando privilégios de administrador")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)