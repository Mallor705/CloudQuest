# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Views para a interface grafica do QuestConfig.
"""

import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from ..core.game import Game
from ..core.config import AppConfigService
from ..services.steam import SteamService
from ..services.shortcut import ShortcutCreatorService
from ..utils.logger import write_log, get_timestamped_message
from ..utils.text_utils import normalize_game_name, sanitize_process_name


class ToolTip:
    """Classe para criar tooltips nos widgets."""
    
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
        
        self.tw = ctk.CTkToplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(self.tw, text=self.text, fg_color="#ffffe0", corner_radius=0)
        label.pack()

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


class QuestConfigView:
    """View principal da aplicacao QuestConfig."""
    
    def __init__(self, root, app_paths, config_service=None, steam_service=None, 
                 pcgamingwiki_service=None, shortcut_service=None):
        """
        Inicializa a interface grafica.
        
        Args:
            root (ctk.CTk): Objeto raiz do CustomTkinter
            app_paths (dict): Dicionario com os caminhos da aplicacao
            config_service: Servico de configuracao
            steam_service: Servico para informacoes da Steam
            pcgamingwiki_service: Servico para informacoes do PCGamingWiki
            shortcut_service: Servico para criacao de atalhos
        """
        self.root = root
        self.app_paths = app_paths
        self.root.geometry("1000x600")
        self.root.resizable(True, True)
        
        # Inicializar servicos
        from ..services import ServiceFactory
        factory = ServiceFactory()
        
        self.config_service = config_service or factory.create_config_service(app_paths)
        self.steam_service = steam_service or factory.create_game_info_service("steam")
        self.pcgamingwiki_service = pcgamingwiki_service or factory.create_game_info_service("pcgamingwiki")
        self.shortcut_service = shortcut_service or factory.create_shortcut_service(app_paths.get('batch_path'))
        
        # Variaveis de entrada
        self.executable_path = ctk.StringVar()
        self.app_id = ctk.StringVar()
        self.game_name = ctk.StringVar()
        self.rclone_path = ctk.StringVar()
        self.cloud_remote = ctk.StringVar()
        self.local_dir = ctk.StringVar()
        self.cloud_dir = ctk.StringVar()
        self.game_process = ctk.StringVar()
        
        # Variaveis de controle
        self.game_name_internal = ""
        self.current_section = ctk.StringVar(value="game_info")  # Seção atual selecionada
        self.current_item = ctk.StringVar()  # Item atual selecionado dentro da seção
        
        # Status
        self.status_var = ctk.StringVar()
        self.status_var.set("Pronto")
        
        # Carregar valores padroes
        self.load_defaults()
        
        # Adicionar trace para atualizar o diretorio cloud quando o local mudar
        self.local_dir.trace_add("write", lambda *_: self.update_cloud_dir())
        
        # Adicionar trace para sanitizar o nome do processo
        self.game_process.trace_add("write", lambda *_: self.sanitize_process_input())
        
        # Mapeamento de campos para descrições
        self.field_descriptions = {
            "executable": {
                "title": "Executável do Jogo",
                "text": "Selecione o arquivo executável (.exe) principal do jogo que você deseja configurar para sincronização na nuvem."
            },
            "appid": {
                "title": "Steam AppID",
                "text": "Identifique o jogo na Steam usando seu AppID único. Este número permite que o sistema localize informações específicas sobre o jogo."
            },
            "game_name": {
                "title": "Nome do Jogo",
                "text": "Forneça o nome completo do jogo para identificação nos registros e arquivos de configuração."
            },
            "save_dir": {
                "title": "Diretório do Save",
                "text": "Indique o diretório onde o jogo armazena seus arquivos de salvamento. Este é o local que será sincronizado com a nuvem."
            },
            "process": {
                "title": "Processo do Jogo",
                "text": "Nome do processo executável do jogo no Gerenciador de Tarefas. Usado para detectar quando o jogo é iniciado ou encerrado."
            },
            "rclone_path": {
                "title": "Caminho do Rclone",
                "text": "Especifique o caminho para o executável do Rclone que será utilizado para sincronizar seus saves de jogos com a nuvem."
            },
            "cloud_remote": {
                "title": "Cloud Remote",
                "text": "Selecione o remote do Rclone já configurado que será usado para armazenar os saves na nuvem (ex: gdrive, onedrive, etc.)."
            },
            "cloud_dir": {
                "title": "Diretório na Nuvem",
                "text": "Defina o caminho dentro do seu armazenamento na nuvem onde os saves serão armazenados."
            }
        }
        
        # Criar widgets
        self.create_widgets()
        
        # Mostrar o painel inicial (após a criação completa da interface)
        self.root.after(100, lambda: self.show_section("game_info"))
        
        write_log("Interface grafica inicializada")
    
    def load_defaults(self):
        """Carrega valores padroes para os campos."""
        defaults = self.config_service.get_default_values()
        self.rclone_path.set(defaults['rclone_path'])
    
    def create_widgets(self):
        """Cria todos os widgets da interface."""
        # Frame principal - usamos um grid layout para organizar dois frames lado a lado
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=3)
        self.main_container.grid_columnconfigure(1, weight=2)
        
        # Frame esquerdo (escuro - contém o formulário)
        self.left_frame = ctk.CTkFrame(self.main_container, fg_color="#292929", corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        # Frame direito (branco - descrições)
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color="white", corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Criar conteúdo do painel direito (descrição)
        self.description_title = ctk.CTkLabel(self.right_frame, text="Executável do Jogo", 
                                           font=("Segoe UI", 16, "bold"), anchor="w")
        self.description_title.pack(anchor="w", pady=(20, 10), padx=20)
        
        self.description_text = ctk.CTkLabel(self.right_frame, 
                                       text="Selecione o arquivo executável (.exe) principal do jogo que você deseja configurar para sincronização na nuvem.", 
                                       wraplength=250, anchor="w")
        self.description_text.pack(anchor="w", padx=20)
        
        # Criar seções
        self.create_section_frames()
        
        # Barra de status
        status_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        status_frame.pack(fill="x", side="bottom", pady=5)
        
        ctk.CTkLabel(status_frame, textvariable=self.status_var).pack(side="left", padx=10)
        
        # Progresso e botões de navegação
        self.progress_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.progress_frame.pack(fill="x", side="bottom", padx=20, pady=10)
        
        # Barra de progresso horizontal
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, orientation="horizontal")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 20))
        
        # Botões de navegação
        self.next_button = ctk.CTkButton(self.progress_frame, text="Próximo", 
                                     command=self.navigate_next, width=120)
        self.next_button.pack(side="right")
        
        self.back_button = ctk.CTkButton(self.progress_frame, text="Voltar", 
                                     command=self.navigate_back, width=120)
        self.back_button.pack(side="right", padx=(0, 10))
        self.back_button.configure(state="disabled")  # Inicialmente desabilitado na primeira tela
    
    def create_section_frames(self):
        """Cria os frames de seção com o conteúdo principal."""
        # Dicionário para armazenar os frames de seção
        self.section_frames = {}
        
        # Seção 1: Informações do Jogo
        game_frame = ctk.CTkFrame(self.left_frame, fg_color="#292929", corner_radius=0)
        
        # Título
        ctk.CTkLabel(game_frame, text="Informações do Jogo", 
                 font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", pady=(20, 20), padx=20)
        
        # Container para os campos do formulário
        form_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20)
        
        # Executável
        ctk.CTkLabel(form_frame, text="Executável do Jogo", text_color="white").pack(anchor="w", pady=(0, 5))
        exe_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        exe_frame.pack(fill="x", pady=(0, 15))
        exe_entry = ctk.CTkEntry(exe_frame, textvariable=self.executable_path, width=400)
        exe_entry.pack(side="left", fill="x", expand=True)
        self.bind_click_and_focus(exe_entry, "executable")
        ctk.CTkButton(exe_frame, text="Procurar...", command=self.browse_executable).pack(side="right", padx=(5, 0))
        
        # AppID
        ctk.CTkLabel(form_frame, text="Steam AppID", text_color="white").pack(anchor="w", pady=(0, 5))
        appid_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        appid_frame.pack(fill="x", pady=(0, 15))
        appid_entry = ctk.CTkEntry(appid_frame, textvariable=self.app_id, width=150)
        appid_entry.pack(side="left")
        self.bind_click_and_focus(appid_entry, "appid")
        ctk.CTkButton(appid_frame, text="Detectar", command=self.detect_appid).pack(side="left", padx=(5, 0))
        ctk.CTkButton(appid_frame, text="Consultar Steam API", command=self.query_steam_api).pack(side="right")
        
        # Nome do Jogo
        ctk.CTkLabel(form_frame, text="Nome do Jogo", text_color="white").pack(anchor="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(form_frame, textvariable=self.game_name, width=400)
        name_entry.pack(fill="x", pady=(0, 15))
        self.bind_click_and_focus(name_entry, "game_name")
        
        # Diretório do Save
        ctk.CTkLabel(form_frame, text="Diretório do Local do Save", text_color="white").pack(anchor="w", pady=(0, 5))
        save_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        save_frame.pack(fill="x", pady=(0, 15))
        save_entry = ctk.CTkEntry(save_frame, textvariable=self.local_dir, width=400)
        save_entry.pack(side="left", fill="x", expand=True)
        self.bind_click_and_focus(save_entry, "save_dir")
        ctk.CTkButton(save_frame, text="Procurar...", command=self.browse_local_dir).pack(side="right", padx=(5, 0))
        
        # Processo do Jogo
        ctk.CTkLabel(form_frame, text="Processo do Jogo", text_color="white").pack(anchor="w", pady=(0, 5))
        process_entry = ctk.CTkEntry(form_frame, textvariable=self.game_process, width=400)
        process_entry.pack(fill="x")
        self.bind_click_and_focus(process_entry, "process")
        
        # Adicionar aos dicionários
        self.section_frames["game_info"] = game_frame
        
        # Seção 2: Configuração Rclone
        rclone_frame = ctk.CTkFrame(self.left_frame, fg_color="#292929", corner_radius=0)
        
        # Título
        ctk.CTkLabel(rclone_frame, text="Configuração Rclone", 
                 font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", pady=(20, 20), padx=20)
        
        # Container para os campos do formulário
        rform_frame = ctk.CTkFrame(rclone_frame, fg_color="transparent")
        rform_frame.pack(fill="both", expand=True, padx=20)
        
        # Caminho do Rclone
        ctk.CTkLabel(rform_frame, text="Caminho do Rclone", text_color="white").pack(anchor="w", pady=(0, 5))
        rclone_path_frame = ctk.CTkFrame(rform_frame, fg_color="transparent")
        rclone_path_frame.pack(fill="x", pady=(0, 15))
        rclone_entry = ctk.CTkEntry(rclone_path_frame, textvariable=self.rclone_path, width=400)
        rclone_entry.pack(side="left", fill="x", expand=True)
        self.bind_click_and_focus(rclone_entry, "rclone_path")
        ctk.CTkButton(rclone_path_frame, text="Procurar...", command=self.browse_rclone).pack(side="right", padx=(5, 0))
        
        # Cloud Remote
        ctk.CTkLabel(rform_frame, text="Cloud Remote", text_color="white").pack(anchor="w", pady=(0, 5))
        remote_frame = ctk.CTkFrame(rform_frame, fg_color="transparent")
        remote_frame.pack(fill="x", pady=(0, 15))
        self.remote_combo = ctk.CTkComboBox(remote_frame, variable=self.cloud_remote, width=300, values=[])
        self.remote_combo.pack(side="left", fill="x", expand=True)
        self.bind_click_and_focus(self.remote_combo, "cloud_remote")
        ctk.CTkButton(remote_frame, text="Detectar", command=self.detect_remotes).pack(side="right", padx=(5, 0))
        
        # Diretório do Save na Nuvem
        ctk.CTkLabel(rform_frame, text="Diretório do Save na Nuvem", text_color="white").pack(anchor="w", pady=(0, 5))
        cloud_entry = ctk.CTkEntry(rform_frame, textvariable=self.cloud_dir, width=400)
        cloud_entry.pack(fill="x", pady=(0, 15))
        self.bind_click_and_focus(cloud_entry, "cloud_dir")
        
        # Checkbox para atalhos
        self.create_shortcut_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(rform_frame, text="Atalho na Área de Trabalho", 
                       variable=self.create_shortcut_var).pack(anchor="w", pady=(10, 0))
        
        self.create_steam_shortcut_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(rform_frame, text="Atalho na Steam", 
                       variable=self.create_steam_shortcut_var).pack(anchor="w")
        
        # Adicionar aos dicionários
        self.section_frames["rclone_config"] = rclone_frame
    
    def bind_click_and_focus(self, widget, field_name):
        """Vincula eventos de clique e foco para atualizar descrições."""
        # Função de callback para atualizar a descrição
        def update_callback(event):
            self.status_var.set(f"Campo selecionado: {field_name}")
            self.update_description_for_field(field_name)
            return True  # Continuar processamento de eventos
        
        # Adicionar bindings para FocusIn, ButtonPress (clique) e Return (seleção)
        widget.bind("<FocusIn>", update_callback)
        widget.bind("<ButtonPress-1>", update_callback)
        widget.bind("<Return>", update_callback)
        
        # Para combobox, adicionar binding especial para quando o menu dropdown é exibido
        if isinstance(widget, ctk.CTkComboBox):
            widget.bind("<<ComboboxSelected>>", update_callback)
    
    def update_description_for_field(self, field_name):
        """Atualiza a descrição com base no campo selecionado."""
        if field_name in self.field_descriptions:
            info = self.field_descriptions[field_name]
            self.update_description(info["title"], info["text"])
    
    def show_section(self, section_id):
        """Mostra uma seção específica e esconde as outras."""
        self.current_section.set(section_id)
        
        # Esconder todos os frames de seção
        for frame in self.section_frames.values():
            frame.pack_forget()
        
        # Mostrar a seção selecionada
        if section_id in self.section_frames:
            self.section_frames[section_id].pack(fill="both", expand=True)
            
        # Atualizar descrição inicial para a seção
        if section_id == "game_info":
            self.update_description("Executável do Jogo", 
                                   "Selecione o arquivo executável (.exe) principal do jogo que você deseja configurar para sincronização na nuvem.")
            # Desabilitar botão de voltar na primeira tela
            self.back_button.configure(state="disabled")
        elif section_id == "rclone_config":
            self.update_description("Caminho do Rclone", 
                                   "Especifique o caminho para o executável do Rclone que será utilizado para sincronizar seus saves de jogos com a nuvem.")
            # Habilitar botão de voltar na segunda tela
            self.back_button.configure(state="normal")
        
        # Atualizar barra de progresso se existir
        if hasattr(self, 'progress_bar'):
            section_order = ["game_info", "rclone_config"]
            progress = (section_order.index(section_id) + 1) * 100 / len(section_order)
            self.progress_bar.set(progress / 100)
        
        # Atualizar texto do botão
        if hasattr(self, 'next_button'):
            section_order = ["game_info", "rclone_config"]
            if section_id == section_order[-1]:  # Se for a última seção
                self.next_button.configure(text="Salvar")
            else:
                self.next_button.configure(text="Próximo")
    
    def update_description(self, title, description_text):
        """Atualiza o título e o texto de descrição no painel direito."""
        # Atualizar o conteúdo
        self.description_title.configure(text=title)
        self.description_text.configure(text=description_text)
    
    def navigate_next(self):
        """Navega para a próxima seção."""
        current = self.current_section.get()
        section_order = ["game_info", "rclone_config"]
        
        if current == "game_info":
            self.show_section("rclone_config")
        elif current == "rclone_config":
            self.save_configuration()
            
    def navigate_back(self):
        """Navega para a seção anterior."""
        current = self.current_section.get()
        
        if current == "rclone_config":
            self.show_section("game_info")
    
    def show_game_info(self):
        """Mostra o primeiro item das informações do jogo."""
        self.show_section("game_info")
    
    def browse_executable(self):
        """Abre dialogo para selecionar o executavel do jogo."""
        filename = filedialog.askopenfilename(
            title="Selecionar Executavel do Jogo",
            filetypes=[("Executaveis", "*.exe"), ("Todos Arquivos", "*.*")]
        )
        
        if filename:
            self.executable_path.set(filename)
            
            # Tentar preencher o nome do processo automaticamente
            exe_name = Path(filename).name
            if not self.game_process.get():
                self.game_process.set(exe_name)
    
    def sanitize_process_input(self):
        """Sanitiza o nome do processo."""
        sanitized = sanitize_process_name(self.game_process.get())
        if sanitized != self.game_process.get():
            self.game_process.set(sanitized)
    
    def browse_rclone(self):
        """Abre dialogo para selecionar o executavel do rclone."""
        filename = filedialog.askopenfilename(
            title="Selecionar Executavel do Rclone",
            filetypes=[("Executaveis", "*.exe"), ("Todos Arquivos", "*.*")]
        )
        
        if filename:
            self.rclone_path.set(filename)
    
    def browse_local_dir(self):
        """Abre dialogo para selecionar o diretorio local de saves."""
        directory = filedialog.askdirectory(
            title="Selecionar Diretorio de Saves"
        )
        
        if directory:
            self.local_dir.set(directory)
    
    def detect_remotes(self):
        """Detecta remotes configurados no Rclone."""
        self.status_var.set("Detectando remotes...")
        self.root.update_idletasks()
        
        def run_detection():
            try:
                remotes = self.config_service.load_rclone_remotes()
                self.root.after(0, lambda: self.update_remotes_result(remotes))
            except Exception as e:
                self.status_var.set("Erro na deteccao")
                messagebox.showerror("Erro", f"Falha ao detectar remotes: {str(e)}")
        
        # Executar em thread separada
        threading.Thread(target=run_detection, daemon=True).start()
    
    def update_remotes_result(self, remotes):
        """Atualiza o resultado da deteccao de remotes."""
        if remotes:
            self.remote_combo.configure(values=remotes)
            
            if remotes and not self.cloud_remote.get():
                self.cloud_remote.set(remotes[0])
            
            self.status_var.set(f"{len(remotes)} remotes detectados")
        else:
            self.remote_combo.configure(values=[])
            self.status_var.set("Nenhum remote detectado")
            messagebox.showwarning("Aviso", "Nenhum remote Rclone foi encontrado. Verifique a configuracao do Rclone.")
    
    def query_steam_api(self):
        """Consulta a API da Steam para obter informacoes do jogo."""
        app_id = self.app_id.get()
        
        if not app_id:
            messagebox.showwarning("Aviso", "Insira um AppID valido primeiro.")
            return
        
        self.status_var.set("Consultando API Steam...")
        self.root.update_idletasks()
        
        def run_query():
            try:
                game_info = self.steam_service.fetch_game_info(app_id)
                self.root.after(0, lambda: self.update_steam_info(game_info))
            except Exception as e:
                self.status_var.set("Erro na consulta")
                messagebox.showerror("Erro", f"Falha na consulta a API Steam: {str(e)}")
        
        # Executar em thread separada
        threading.Thread(target=run_query, daemon=True).start()
    
    def update_steam_info(self, game_info):
        """Atualiza as informacoes do jogo com dados da Steam."""
        if not game_info:
            self.status_var.set("Informacoes nao encontradas na Steam")
            messagebox.showinfo("Informacao", "Nao foi possivel obter informacoes do jogo na Steam.")
            return
        
        # Atualizar campos
        self.game_name.set(game_info['name'])
        self.game_name_internal = game_info['internal_name']
        
        # Atualizar local de save se disponivel
        if game_info.get('save_location'):
            self.local_dir.set(game_info['save_location'])
        
        self.status_var.set(f"Informacoes obtidas para {game_info['name']}")
        
        # Atualizar diretorio cloud
        self.update_cloud_dir()
    
    def detect_appid(self):
        """Detecta o AppID do jogo a partir do executavel."""
        exe_path = self.executable_path.get()
        
        if not exe_path or not Path(exe_path).exists():
            messagebox.showwarning("Aviso", "Selecione um executavel valido primeiro.")
            return
        
        self.status_var.set("Detectando AppID...")
        self.root.update_idletasks()
        
        def run_detection():
            try:
                app_id = self.steam_service.detect_appid_from_file(exe_path)
                self.root.after(0, lambda: self.update_appid_result(app_id))
            except Exception as e:
                self.status_var.set("Erro na deteccao")
                messagebox.showerror("Erro", f"Falha ao detectar AppID: {str(e)}")
        
        # Executar em thread separada
        threading.Thread(target=run_detection, daemon=True).start()
    
    def update_appid_result(self, app_id):
        """Atualiza o resultado da deteccao de AppID."""
        if app_id:
            self.app_id.set(app_id)
            self.status_var.set(f"AppID detectado: {app_id}")
        else:
            self.status_var.set("AppID nao detectado")
            messagebox.showinfo("Informacao", "Nao foi possivel detectar o AppID automaticamente. Por favor, insira manualmente.")
    
    def update_cloud_dir(self):
        """Atualiza o diretorio cloud com base no diretorio local."""
        local_dir = self.local_dir.get()
        game_name = self.game_name.get()
        
        if not local_dir or not game_name:
            return
        
        # Normalizar nome do jogo para uso interno
        if not self.game_name_internal:
            self.game_name_internal = normalize_game_name(game_name)
        
        # Extrair o ultimo segmento do caminho local (geralmente o ID do usuario)
        path = Path(local_dir.rstrip('/\\'))
        last_segment = path.parts[-1] if path.parts else None
        
        # Montar o caminho cloud baseado no nome interno do jogo e no ultimo segmento
        cloud_path = f"CloudQuest/{self.game_name_internal}/"
        
        # Se tiver um ultimo segmento (ID do usuario), adiciona-lo ao caminho na nuvem
        if last_segment:
            cloud_path = f"CloudQuest/{self.game_name_internal}/{last_segment}/"
        
        self.cloud_dir.set(cloud_path)
    
    def save_configuration(self):
        """Salva a configuracao do jogo."""
        # Validar campos obrigatorios
        if not self.validate_required_fields():
            return
        
        # Obter dados do jogo
        game_data = self.get_game_data()
        
        # Salvar configuracao
        config_file = self.config_service.save_game_config(game_data, self.app_paths['profiles_dir'])
        
        if config_file:
            self.status_var.set(f"Configuracao salva: {config_file}")
            
            # Criar atalho se solicitado
            if self.create_shortcut_var.get():
                success = self.shortcut_service.create_game_shortcut(game_data)
                if success:
                    messagebox.showinfo("Sucesso", "Configuracao salva e atalho criado com sucesso!")
                else:
                    messagebox.showwarning("Aviso", "Configuracao salva, mas houve um erro ao criar o atalho.")
            else:
                messagebox.showinfo("Sucesso", "Configuracao salva com sucesso!")
        else:
            self.status_var.set("Erro ao salvar configuracao")
            messagebox.showerror("Erro", "Nao foi possivel salvar a configuracao do jogo.")
    
    def validate_required_fields(self):
        """Valida os campos obrigatorios."""
        required_fields = [
            (self.game_name.get(), "Nome do Jogo"),
            (self.executable_path.get(), "Executavel do Jogo"),
            (self.game_process.get(), "Processo do Jogo"),
            (self.local_dir.get(), "Diretorio Local"),
            (self.cloud_remote.get(), "Cloud Remote"),
            (self.cloud_dir.get(), "Diretorio Cloud")
        ]
        
        missing = []
        for value, name in required_fields:
            if not value.strip():
                missing.append(name)
        
        if missing:
            messagebox.showwarning("Campos Obrigatorios", 
                                  f"Por favor, preencha os seguintes campos:\n- {'\n- '.join(missing)}")
            return False
        
        return True
    
    def get_game_data(self):
        """Obtem os dados do jogo a partir dos campos do formulario."""
        if not self.game_name_internal:
            self.game_name_internal = normalize_game_name(self.game_name.get())
        
        game = Game(
            name=self.game_name.get(),
            internal_name=self.game_name_internal,
            app_id=self.app_id.get(),
            platform="Steam",
            executable_path=self.executable_path.get(),
            process_name=self.game_process.get(),
            save_location=self.local_dir.get(),
            cloud_remote=self.cloud_remote.get(),
            cloud_dir=self.cloud_dir.get()
        )
        
        # Converter para dicionário e adicionar o caminho do rclone
        game_dict = game.to_dict()
        game_dict['RclonePath'] = self.rclone_path.get()
        
        return game_dict
        
    def reset_form(self):
        """Limpa todos os campos do formulario."""
        if messagebox.askyesno("Confirmar", "Deseja limpar todos os campos?"):
            self.executable_path.set("")
            self.app_id.set("")
            self.game_name.set("")
            self.local_dir.set("")
            self.cloud_dir.set("")
            self.game_process.set("")
            self.game_name_internal = ""
            
            # Manter valores padrao
            defaults = self.config_service.get_default_values()
            self.rclone_path.set(defaults['rclone_path'])
            
            # Resetar resumo
            if hasattr(self, 'summary_text'):
                self.summary_text.configure(state="normal")
                self.summary_text.delete(1.0, "end")
                self.summary_text.insert("end", "Clique em 'Atualizar Resumo' para ver as configurações")
                self.summary_text.configure(state="disabled")
            
            self.status_var.set("Formulário resetado")
            
            # Voltar para o primeiro item
            self.show_game_info()