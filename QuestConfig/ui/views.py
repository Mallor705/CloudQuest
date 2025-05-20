# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Views para a interface grafica do QuestConfig.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
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
            root (tk.Tk): Objeto raiz do Tkinter
            app_paths (dict): Dicionario com os caminhos da aplicacao
            config_service: Servico de configuracao
            steam_service: Servico para informacoes da Steam
            pcgamingwiki_service: Servico para informacoes do PCGamingWiki
            shortcut_service: Servico para criacao de atalhos
        """
        self.root = root
        self.app_paths = app_paths
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Inicializar servicos
        from ..services import ServiceFactory
        factory = ServiceFactory()
        
        self.config_service = config_service or factory.create_config_service(app_paths)
        self.steam_service = steam_service or factory.create_game_info_service("steam")
        self.pcgamingwiki_service = pcgamingwiki_service or factory.create_game_info_service("pcgamingwiki")
        self.shortcut_service = shortcut_service or factory.create_shortcut_service(app_paths.get('batch_path'))
        
        # Variaveis de entrada
        self.executable_path = tk.StringVar()
        self.app_id = tk.StringVar()
        self.game_name = tk.StringVar()
        self.rclone_path = tk.StringVar()
        self.cloud_remote = tk.StringVar()
        self.local_dir = tk.StringVar()
        self.cloud_dir = tk.StringVar()
        self.game_process = tk.StringVar()
        
        # Variaveis de controle
        self.game_name_internal = ""
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        
        # Carregar valores padroes
        self.load_defaults()
        
        # Criar widgets
        self.create_widgets()
        
        # Adicionar trace para atualizar o diretorio cloud quando o local mudar
        self.local_dir.trace_add("write", lambda *_: self.update_cloud_dir())
        
        # Adicionar trace para sanitizar o nome do processo
        self.game_process.trace_add("write", lambda *_: self.sanitize_process_input())
        
        write_log("Interface grafica inicializada")
    
    def load_defaults(self):
        """Carrega valores padroes para os campos."""
        defaults = self.config_service.get_default_values()
        self.rclone_path.set(defaults['rclone_path'])
    
    def create_widgets(self):
        """Cria todos os widgets da interface."""
        # Estilo
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10))
        self.style.configure('TEntry', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
                
        main_frame = ttk.Frame(self.root, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para organizar as etapas em abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Criar as abas
        self.create_game_info_tab()
        self.create_sync_config_tab()
        self.create_finish_tab()
        
        # Barra de status
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)
    
    def create_game_info_tab(self):
        """Cria a aba de informacoes do jogo."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="1. Informacoes do Jogo")
        
        # Titulo da secao
        header = ttk.Label(tab, text="Informacoes do Jogo", style='Header.TLabel')
        header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Executavel
        ttk.Label(tab, text="Executavel do Jogo:").grid(row=1, column=0, sticky="w", pady=2)
        exe_frame = ttk.Frame(tab)
        exe_frame.grid(row=1, column=1, sticky="ew", pady=2)
        
        ttk.Entry(exe_frame, textvariable=self.executable_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(exe_frame, text="Procurar...", command=self.browse_executable).pack(side=tk.RIGHT, padx=(5, 0))
        
        # AppID
        ttk.Label(tab, text="AppID Steam:").grid(row=2, column=0, sticky="w", pady=2)
        appid_frame = ttk.Frame(tab)
        appid_frame.grid(row=2, column=1, sticky="ew", pady=2)
        
        ttk.Entry(appid_frame, textvariable=self.app_id, width=20).pack(side=tk.LEFT)
        ttk.Button(appid_frame, text="Detectar", command=self.detect_appid).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(appid_frame, text="Consultar Steam", command=self.query_steam_api).pack(side=tk.LEFT, padx=(5, 0))
        
        # Nome do Jogo
        ttk.Label(tab, text="Nome do Jogo:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(tab, textvariable=self.game_name, width=50).grid(row=3, column=1, sticky="ew", pady=2)
    
    def create_sync_config_tab(self):
        """Cria a aba de configuracao de sincronizacao."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="2. Configuracao Rclone")
        
        # Titulo da secao
        header = ttk.Label(tab, text="Configuracao de Sincronizacao", style='Header.TLabel')
        header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        
        # Rclone
        ttk.Label(tab, text="Caminho do Rclone:").grid(row=1, column=0, sticky="w", pady=2)
        rclone_frame = ttk.Frame(tab)
        rclone_frame.grid(row=1, column=1, sticky="ew", pady=2)
        
        ttk.Entry(rclone_frame, textvariable=self.rclone_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(rclone_frame, text="Procurar...", command=self.browse_rclone).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Remote
        ttk.Label(tab, text="Cloud Remote:").grid(row=2, column=0, sticky="w", pady=2)
        remote_frame = ttk.Frame(tab)
        remote_frame.grid(row=2, column=1, sticky="ew", pady=2)
        
        self.remote_combo = ttk.Combobox(remote_frame, textvariable=self.cloud_remote, width=30)
        self.remote_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(remote_frame, text="Detectar Remotes", command=self.detect_remotes).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Local Dir
        ttk.Label(tab, text="Diretorio Local:").grid(row=3, column=0, sticky="w", pady=2)
        local_dir_frame = ttk.Frame(tab)
        local_dir_frame.grid(row=3, column=1, sticky="ew", pady=2)
        
        ttk.Entry(local_dir_frame, textvariable=self.local_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(local_dir_frame, text="Procurar...", command=self.browse_local_dir).pack(side=tk.RIGHT, padx=(5, 0))
        detect_button = ttk.Button(local_dir_frame, text="Detectar Auto", command=self.detect_save_location)
        detect_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cloud Dir
        ttk.Label(tab, text="Diretorio Cloud:").grid(row=4, column=0, sticky="w", pady=2)
        cloud_dir_frame = ttk.Frame(tab)
        cloud_dir_frame.grid(row=4, column=1, sticky="ew", pady=2)
        
        ttk.Entry(cloud_dir_frame, textvariable=self.cloud_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Processo do jogo
        ttk.Label(tab, text="Processo do Jogo:").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(tab, textvariable=self.game_process, width=50).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(tab, text="(Nome do executavel do jogo, ex: eldenring)").grid(row=5, column=2, sticky="w", padx=(5, 0), pady=2)
    
    def create_finish_tab(self):
        """Cria a aba de finalizacao."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="3. Finalizar")
        
        # Titulo da secao
        header = ttk.Label(tab, text="Resumo da Configuracao", style='Header.TLabel')
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Frame para o resumo
        summary_frame = ttk.LabelFrame(tab, text="Dados da Configuracao")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Texto de resumo
        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=10, width=70)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.insert(tk.END, "Configure as abas anteriores e clique em 'Atualizar Resumo'")
        self.summary_text.config(state=tk.DISABLED)
        
        # Botao para atualizar resumo
        ttk.Button(tab, text="Atualizar Resumo", command=self.update_summary).grid(row=2, column=0, pady=10)
        
        # Opcoes finais
        options_frame = ttk.LabelFrame(tab, text="Opcoes")
        options_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Opcao para criar atalho
        self.create_shortcut_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Criar atalho na area de trabalho", variable=self.create_shortcut_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # Botoes de acao
        buttons_frame = ttk.Frame(tab)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=20)
        
        ttk.Button(buttons_frame, text="Salvar Configuracao", command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpar Campos", command=self.reset_form).pack(side=tk.RIGHT, padx=5)
    
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
    
    def detect_save_location(self):
        """Detecta possiveis localizacoes de saves para o jogo."""
        exe_path = self.executable_path.get()
        
        if not exe_path or not Path(exe_path).exists():
            messagebox.showwarning("Aviso", "Selecione um executavel valido primeiro.")
            return
        
        self.status_var.set("Detectando locais de save...")
        self.root.update_idletasks()
        
        def run_detection():
            try:
                paths = []
                
                # Tentar primeiro via PCGamingWiki se tiver AppID
                app_id = self.app_id.get()
                if app_id:
                    try:
                        # Usar PCGamingWikiService para encontrar saves
                        save_info = self.pcgamingwiki_service.find_save_locations(app_id)
                        if save_info:
                            if save_info.get("existing_paths"):
                                paths.extend(save_info["existing_paths"])
                            if save_info.get("expanded_paths"):
                                paths.extend(save_info["expanded_paths"])
                            
                            if paths:
                                self.status_var.set(f"Locais de save encontrados via PCGamingWiki: {len(paths)}")
                    except Exception as e:
                        write_log(f"Erro ao consultar PCGamingWiki: {str(e)}", level='WARNING')
                
                # Se nao encontrou via PCGamingWiki, usar o SaveDetectorService
                if not paths:
                    try:
                        # Criar uma instancia do SaveDetectorService com o caminho do executavel
                        from ..services import ServiceFactory
                        
                        # Aviso ao usuario
                        self.status_var.set("Iniciando jogo para detectar saves (o jogo sera fechado automaticamente)...")
                        self.root.update_idletasks()
                        
                        # Criar detector com o executavel
                        detector = ServiceFactory.create_save_detector_service(exe_path)
                        if detector:
                            paths = detector.detect_save_location()
                            self.status_var.set("Locais de save detectados")
                        else:
                            self.status_var.set("Nao foi possivel iniciar detector de saves")
                    except Exception as e:
                        write_log(f"Erro ao usar SaveDetectorService: {str(e)}", level='WARNING')
                
                # Mostrar os caminhos encontrados
                self.root.after(0, lambda: self.show_save_paths(paths))
                
            except Exception as e:
                self.status_var.set("Erro na deteccao")
                messagebox.showerror("Erro", f"Falha ao detectar saves: {str(e)}")
        
        # Executar em thread separada
        threading.Thread(target=run_detection, daemon=True).start()
    
    def show_save_paths(self, paths):
        """Mostra dialogo de selecao de caminhos de save."""
        if not paths:
            messagebox.showinfo("Informacao", "Nenhum local de save detectado automaticamente.")
            return
        
        # Criar dialogo de selecao
        dialog = tk.Toplevel(self.root)
        dialog.title("Selecione o Local de Saves")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Selecione o diretorio de saves do jogo:").pack(padx=10, pady=5, anchor=tk.W)
        
        # Frame para lista e preview
        split_frame = ttk.Frame(dialog)
        split_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Lista de caminhos
        path_list = tk.Listbox(split_frame, width=80, height=10)
        path_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(split_frame, orient=tk.VERTICAL, command=path_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        path_list.config(yscrollcommand=scrollbar.set)
        
        # Adicionar caminhos a lista
        for path in paths:
            path_list.insert(tk.END, path)
        
        # Selecao padrao
        if paths:
            path_list.selection_set(0)
        
        # Frame para botoes
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Selecionar", command=lambda: self.select_path()).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        def select_path():
            try:
                selection = path_list.curselection()
                if selection:
                    idx = selection[0]
                    selected_path = paths[idx]
                    self.update_save_location(selected_path)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao selecionar caminho: {str(e)}")
        
        self.select_path = select_path
    
    def update_save_location(self, save_path):
        """Atualiza o campo de local de saves com o caminho selecionado."""
        self.local_dir.set(save_path)
        self.update_cloud_dir()
        
        # Atualizar o status
        self.status_var.set(f"Local de saves definido: {save_path}")
    
    def browse_local_dir(self):
        """Abre dialogo para selecionar o diretorio local de saves."""
        directory = filedialog.askdirectory(
            title="Selecionar Diretorio de Saves"
        )
        
        if directory:
            self.local_dir.set(directory)
    
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
            self.remote_combo['values'] = remotes
            
            if remotes and not self.cloud_remote.get():
                self.cloud_remote.set(remotes[0])
            
            self.status_var.set(f"{len(remotes)} remotes detectados")
        else:
            self.remote_combo['values'] = []
            self.status_var.set("Nenhum remote detectado")
            messagebox.showwarning("Aviso", "Nenhum remote Rclone foi encontrado. Verifique a configuracao do Rclone.")
    
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
    
    def update_summary(self):
        """Atualiza o resumo da configuracao."""
        # Montar resumo
        game_data = self.get_game_data()
        
        summary = f"Nome do Jogo: {game_data.get('name', 'Nao definido')}\n"
        summary += f"AppID Steam: {game_data.get('app_id', 'N/A')}\n"
        summary += f"Executavel: {game_data.get('executable_path', 'Nao definido')}\n"
        summary += f"Processo: {game_data.get('process_name', 'Nao definido')}\n"
        summary += f"Diretorio Local: {game_data.get('save_location', 'Nao definido')}\n"
        summary += f"Remote: {game_data.get('cloud_remote', 'Nao definido')}\n"
        summary += f"Diretorio Cloud: {game_data.get('cloud_dir', 'Nao definido')}\n"
        
        # Atualizar campo de texto
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
    
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
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, "Configure as abas anteriores e clique em 'Atualizar Resumo'")
            self.summary_text.config(state=tk.DISABLED)
            
            self.status_var.set("Formulario resetado")