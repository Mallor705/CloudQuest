#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface gráfica para o QuestConfig.
Implementa a interface de usuário para configuração de jogos.
"""

import os
import re
import threading
import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import Toplevel, Label

from .logger import write_log, get_timestamped_message
from .path_utils import validate_path
from .config import load_rclone_remotes, save_game_config, get_default_values
from .steam_api import detect_appid_from_file, fetch_game_info
from .text_utils import normalize_game_name
from .text_utils import sanitize_process_name
from .shortcut_creator import create_game_shortcut
from .save_detector import SaveGameDetector

# Adicione um tooltip explicativo (opcional):
from tkinter import Toplevel, Label

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        self.tw = Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        label = Label(self.tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

class QuestConfigGUI:
    def __init__(self, root, app_paths):
        """
        Inicializa a interface gráfica
        
        Args:
            root (tk.Tk): Objeto raiz do Tkinter
            app_paths (dict): Dicionário com os caminhos da aplicação
        """
        self.root = root
        self.app_paths = app_paths
        self.root.title("QuestConfig Game Configurator")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.detect_thread = None
        
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

        # Adicionar trace para sanitizar o processo de entrada
        self.game_process.trace_add("write", lambda *_: self.sanitize_process_input())

        write_log("GUI iniciada")
        
    def load_defaults(self):
        """Carrega valores padrões para os campos"""
        defaults = get_default_values()
        self.rclone_path.set(defaults['rclone_path'])
        
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
        detect_button = ttk.Button(local_dir_frame, text="Detectar Auto", command=self.detect_save_location)
        detect_button.pack(side=tk.RIGHT, padx=(5, 0))
        ToolTip(detect_button, "Executa o jogo brevemente e tenta detectar\nonde os saves estão sendo armazenados")

        # Cloud Dir
        ttk.Label(tab2, text="Diretório Cloud:").grid(row=4, column=0, sticky="w", pady=2)
        cloud_dir_frame = ttk.Frame(tab2)
        cloud_dir_frame.grid(row=4, column=1, sticky="ew", pady=2)
        
        ttk.Entry(cloud_dir_frame, textvariable=self.cloud_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Processo do jogo
        ttk.Label(tab2, text="Processo do Jogo:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(tab2, textvariable=self.game_process, width=50).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab2, text="(Nome do .exe, ex: Skyrim.exe)").grid(row=5, column=2, sticky="w", padx=(5, 0), pady=2)
        
        # Aba 3: Resumo e Finalização
        tab3 = ttk.Frame(notebook, padding=10)
        notebook.add(tab3, text="3. Finalizar")
        
        # Título da seção
        header3 = ttk.Label(tab3, text="Resumo da Configuração", style='Header.TLabel')
        header3.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Frame para o resumo
        summary_frame = ttk.LabelFrame(tab3, text="Dados da Configuração")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Texto de resumo
        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=10, width=70)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.insert(tk.END, "Configure as abas anteriores e clique em 'Atualizar Resumo'")
        self.summary_text.config(state=tk.DISABLED)
        
        # Botão para atualizar resumo
        ttk.Button(tab3, text="Atualizar Resumo", command=self.update_summary).grid(row=2, column=0, pady=10)
        
        # Opções finais
        options_frame = ttk.LabelFrame(tab3, text="Opções")
        options_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Opção para criar atalho
        self.create_shortcut_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Criar atalho na área de trabalho", variable=self.create_shortcut_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Botões de ação
        buttons_frame = ttk.Frame(tab3)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=20)
        
        ttk.Button(buttons_frame, text="Salvar Configuração", command=self.save_configuration, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancelar", command=self.reset_form, width=20).pack(side=tk.RIGHT, padx=5)
        
        # Log na parte inferior
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=6, width=80)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        
        # Status bar
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configurar o log para mostrar mensagens na interface
        self.add_log_message("Aplicação iniciada. Preencha os dados do jogo.")
    
    def browse_executable(self):
        """Abre diálogo para selecionar executável do jogo"""
        filename = filedialog.askopenfilename(
            title="Selecionar Executável do Jogo",
            filetypes=[("Executáveis", "*.exe"), ("Todos os Arquivos", "*.*")]
        )
        
        if filename:
            self.executable_path.set(filename)
            self.add_log_message(f"Executável selecionado: {filename}")
            
            # Auto-detectar nome do jogo a partir do nome do arquivo
            game_file = Path(filename).stem
            if not self.game_name.get():
                self.game_name.set(game_file)
            
            # Auto-detectar nome do processo
            if not self.game_process.get():
                game_process_name = Path(filename).stem  # Remove a extensão .exe
                self.game_process.set(game_process_name)
            
            # # Auto-detectar diretório local para saves
            # if not self.local_dir.get():
            #     self.setup_default_local_dir(game_file)
            
            # Atualizar diretório cloud
            self.update_cloud_dir()
    
    def sanitize_process_input(self):
        current_value = self.game_process.get()
        sanitized = sanitize_process_name(current_value)
        if current_value != sanitized:
            self.game_process.set(sanitized)

    def setup_default_local_dir(self, game_name):
        """Define um diretório local padrão para os saves do jogo"""
        documents_dir = Path(os.environ['USERPROFILE']) / "Documents"
        game_dir = documents_dir / f"CloudQuest/{game_name}"
        self.local_dir.set(str(game_dir))
    
    def browse_rclone(self):
        """Abre diálogo para selecionar executável do Rclone"""
        filename = filedialog.askopenfilename(
            title="Selecionar Executável do Rclone",
            filetypes=[("Executáveis", "*.exe"), ("Todos os Arquivos", "*.*")]
        )
        
        if filename:
            self.rclone_path.set(filename)
            self.add_log_message(f"Rclone selecionado: {filename}")
    
    def detect_save_location(self):
        if not validate_path(self.executable_path.get(), 'File'):
            messagebox.showerror("Erro", "Selecione um executável válido primeiro!")
            return
        
        resposta = messagebox.askyesno(
            "Aviso", 
            "O jogo será executado temporariamente. Feche-o manualmente após criar um save.\nContinuar?"
        )
        if not resposta:
            return

        self.status_var.set("Iniciando detecção de saves...")
        self.add_log_message("Iniciando detecção automática de local de saves")

        def run_detection():
            detector = SaveGameDetector(self.executable_path.get())
            save_path = detector.detect_save_location()
            
            self.root.after(0, lambda: self.update_save_location(save_path))
        
        self.detect_thread = threading.Thread(target=run_detection)
        self.detect_thread.start()
    
    def update_save_location(self, save_path):
        if save_path:
            self.local_dir.set(str(save_path))
            self.add_log_message(f"Diretório de save detectado: {save_path}")
            self.status_var.set("Local de save detectado com sucesso")
            messagebox.showinfo("Sucesso", f"Diretório de save detectado:\n{save_path}")
        else:
            self.add_log_message("Não foi possível detectar o local de saves automaticamente")
            self.status_var.set("Falha na detecção de saves")
            messagebox.showwarning("Aviso", "Não foi possível detectar o local de saves automaticamente")

    def browse_local_dir(self):
        """Abre diálogo para selecionar diretório local para saves"""
        directory = filedialog.askdirectory(title="Selecionar Diretório Local para Saves")
        
        if directory:
            self.local_dir.set(directory)
            self.add_log_message(f"Diretório local selecionado: {directory}")
            self.update_cloud_dir()
    
    def detect_appid(self):
        """Detecta AppID a partir do arquivo steam_appid.txt"""
        exe_path = self.executable_path.get()
        
        if not validate_path(exe_path, 'File'):
            messagebox.showerror("Erro", "Selecione um executável válido primeiro.")
            return
        
        self.status_var.set("Detectando AppID...")
        self.add_log_message("Tentando detectar AppID do jogo...")
        
        # Usar thread para não bloquear a interface
        def run_detection():
            app_id = detect_appid_from_file(exe_path)
            
            # Atualizar interface na thread principal
            self.root.after(0, lambda: self.update_appid_result(app_id))
        
        threading.Thread(target=run_detection).start()
    
    def update_appid_result(self, app_id):
        """Atualiza a interface com o resultado da detecção de AppID"""
        if app_id:
            self.app_id.set(app_id)
            self.add_log_message(f"AppID detectado: {app_id}")
            self.status_var.set("AppID detectado com sucesso")
        else:
            self.add_log_message("Não foi possível detectar o AppID automaticamente.")
            self.status_var.set("Falha ao detectar AppID")
    
    def query_steam_api(self):
        """Consulta a API da Steam para obter informações do jogo"""
        app_id = self.app_id.get()
        
        if not app_id:
            messagebox.showerror("Erro", "Digite um AppID válido primeiro.")
            return
        
        self.status_var.set("Consultando API Steam...")
        self.add_log_message(f"Consultando informações para AppID: {app_id}...")
        
        # Usar thread para não bloquear a interface
        def run_query():
            game_info = fetch_game_info(app_id)
            
            # Atualizar interface na thread principal
            self.root.after(0, lambda: self.update_steam_info(game_info))
        
        threading.Thread(target=run_query).start()
    
    def update_steam_info(self, game_info):
        """Atualiza a interface com as informações obtidas da Steam"""
        if game_info:
            self.game_name.set(game_info['name'])
            self.game_name_internal = game_info['internal_name']
            
            # Atualizar diretórios
            if not self.local_dir.get():
                self.setup_default_local_dir(self.game_name_internal)
            
            self.update_cloud_dir()
            
            self.add_log_message(f"Dados obtidos: {game_info['name']} (ID interno: {self.game_name_internal})")
            self.status_var.set("Informações obtidas com sucesso")
        else:
            self.add_log_message("Não foi possível obter informações do jogo da Steam.")
            self.status_var.set("Falha ao consultar Steam")
    
    def detect_remotes(self):
        """Detecta remotes configurados no Rclone"""
        self.status_var.set("Detectando remotes...")
        self.add_log_message("Detectando remotes do Rclone...")
        
        # Usar thread para não bloquear a interface
        def run_detection():
            remotes = load_rclone_remotes()
            
            # Atualizar interface na thread principal
            self.root.after(0, lambda: self.update_remotes_result(remotes))
        
        threading.Thread(target=run_detection).start()
    
    def update_remotes_result(self, remotes):
        """Atualiza a interface com os remotes detectados"""
        if remotes:
            self.remote_combo['values'] = remotes
            
            # Selecionar primeiro remote se nenhum estiver selecionado
            if not self.cloud_remote.get() and remotes:
                self.cloud_remote.set(remotes[0])
                self.update_cloud_dir()
            
            self.add_log_message(f"Remotes detectados: {', '.join(remotes)}")
            self.status_var.set("Remotes detectados com sucesso")
        else:
            self.add_log_message("Nenhum remote do Rclone encontrado. Verifique a instalação do Rclone.")
            self.status_var.set("Nenhum remote encontrado")
    
    def update_cloud_dir(self):
        """Atualiza o diretório cloud com base no diretório final do caminho local"""
        local_dir = self.local_dir.get()
        
        if local_dir:
            # Extrair o nome do diretório final do caminho local
            final_dir_name = Path(local_dir).name
            
            # Criar caminho cloud com o formato 'CloudQuest/{nome_do_diretório_final}'
            cloud_path = f"CloudQuest/{final_dir_name}"
            self.cloud_dir.set(cloud_path)
            self.add_log_message(f"Diretório cloud atualizado: {cloud_path}")
        elif self.game_name_internal:
            # Caso fallback se não houver diretório local
            cloud_path = f"CloudQuest/{self.game_name_internal}"
            self.cloud_dir.set(cloud_path)
            self.add_log_message(f"Diretório cloud atualizado: {cloud_path}")
        elif self.game_name.get():
            # Segundo fallback usando o nome normalizado do jogo
            norm_name = normalize_game_name(self.game_name.get())
            cloud_path = f"CloudQuest/{norm_name}"
            self.cloud_dir.set(cloud_path)
            self.add_log_message(f"Diretório cloud atualizado: {cloud_path}")
    
    def update_summary(self):
        """Atualiza o resumo da configuração"""
        # Obter nome interno se ainda não foi definido
        if not self.game_name_internal and self.game_name.get():
            self.game_name_internal = normalize_game_name(self.game_name.get())
        
        # Criar resumo
        summary = f"""Nome do Jogo: {self.game_name.get()}
                Nome Interno: {self.game_name_internal}
                AppID Steam: {self.app_id.get()}
                Executável: {self.executable_path.get()}
                Processo: {self.game_process.get()}

                Configuração Rclone:
                - Remote: {self.cloud_remote.get()}
                - Diretório Local: {self.local_dir.get()}
                - Diretório Cloud: {self.cloud_dir.get()}

                Criar atalho: {"Sim" if self.create_shortcut_var.get() else "Não"}
                """
        
        # Atualizar widget de texto
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
        
        self.add_log_message("Resumo atualizado")
        return summary
    
    def save_configuration(self):
        """Salva a configuração do jogo"""
        # Verificar campos obrigatórios
        if not self.validate_required_fields():
            return
        
        # Atualizar nome interno se necessário
        if not self.game_name_internal and self.game_name.get():
            self.game_name_internal = normalize_game_name(self.game_name.get())
        
        # Preparar dados de configuração
        config_data = {
            "GameName": self.game_name.get(),
            "InternalName": self.game_name_internal,
            "AppID": self.app_id.get(),
            "ExecutablePath": self.executable_path.get(),
            "GameProcess": sanitize_process_name(self.game_process.get()),
            "RclonePath": self.rclone_path.get(),
            "CloudRemote": self.cloud_remote.get(),
            "LocalDir": self.local_dir.get(),
            "CloudDir": self.cloud_dir.get(),
            "CreateShortcut": self.create_shortcut_var.get(),
            "Created": datetime.datetime.now().isoformat()
        }
        
        # Salvar configuração
        config_file = save_game_config(config_data, self.app_paths['profiles_dir'])
        
        if config_file:
            self.add_log_message(f"Configuração salva com sucesso em: {config_file}")
            
            # Criar atalho se solicitado
            if self.create_shortcut_var.get():
                if create_game_shortcut(config_data, self.app_paths['batch_path']):
                    self.add_log_message(f"Atalho criado para: {self.game_name.get()}")
                else:
                    self.add_log_message("Falha ao criar atalho na área de trabalho", level='WARNING')
            
            messagebox.showinfo("Concluído", f"Configuração para '{self.game_name.get()}' salva com sucesso!")
            
            # Resetar formulário
            self.reset_form()
        else:
            messagebox.showerror("Erro", "Ocorreu um erro ao salvar a configuração.")
            self.add_log_message("Falha ao salvar configuração", level='ERROR')
    
    def validate_required_fields(self):
        """Valida os campos obrigatórios antes de salvar"""
        missing_fields = []
        
        if not self.game_name.get():
            missing_fields.append("Nome do Jogo")
        
        if not self.executable_path.get() or not validate_path(self.executable_path.get(), 'File'):
            missing_fields.append("Executável do Jogo (arquivo válido)")
        
        if not self.rclone_path.get() or not validate_path(self.rclone_path.get(), 'File'):
            missing_fields.append("Caminho do Rclone (arquivo válido)")
        
        if not self.cloud_remote.get():
            missing_fields.append("Cloud Remote")
        
        if not self.local_dir.get():
            missing_fields.append("Diretório Local")
        
        if not self.cloud_dir.get():
            missing_fields.append("Diretório Cloud")
        
        game_process = sanitize_process_name(self.game_process.get())
        if not game_process:
            missing_fields.append("Processo do Jogo")

        if missing_fields:
            messagebox.showerror("Campos Obrigatórios", 
                                "Os seguintes campos são obrigatórios:\n" + 
                                "\n".join([f"- {field}" for field in missing_fields]))
            return False
        
        return True
    
    def reset_form(self):
        """Limpa o formulário para nova configuração"""
        self.executable_path.set("")
        self.app_id.set("")
        self.game_name.set("")
        self.game_name_internal = ""
        self.local_dir.set("")
        self.cloud_dir.set("")
        self.game_process.set("")
        
        # Limpar resumo
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, "Configure as abas anteriores e clique em 'Atualizar Resumo'")
        self.summary_text.config(state=tk.DISABLED)
        
        self.add_log_message("Formulário reiniciado para nova configuração")
        self.status_var.set("Pronto")
    
    def add_log_message(self, message, level='INFO'):
        """Adiciona mensagem ao log na interface"""
        if self.log_text:
            timestamped_msg = get_timestamped_message(message)
            
            # Definir cor com base no nível
            if level == 'ERROR':
                tag = 'error'
                color = 'red'
            elif level == 'WARNING':
                tag = 'warning'
                color = 'orange'
            else:
                tag = 'info'
                color = 'black'
            
            # Adicionar texto
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, timestamped_msg + "\n", tag)
            self.log_text.tag_configure(tag, foreground=color)
            self.log_text.see(tk.END)  # Rolar para o final
            self.log_text.configure(state='disabled')
        
        # Registrar no sistema de log
        write_log(message, level)