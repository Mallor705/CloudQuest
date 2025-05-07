# modules/profile_selector.py
# SELETOR DE PERFIL
# ====================================================
import os
import sys
import json
import tempfile
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from .config import write_log, cloud_quest_root

class ProfileSelector:
    """Interface gráfica para selecionar perfis do CloudQuest"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CloudQuest - Seletor de Perfil")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Configura o estilo
        self.configure_style()
        
        # Centraliza a janela
        self.center_window()
        
        # Coloca em primeiro plano
        self.root.attributes("-topmost", True)
        
        # Carrega os perfis disponíveis
        self.profiles = self.load_profiles()
        
        # Constrói a interface
        self.build_interface()
    
    def configure_style(self):
        """Configura o estilo visual da interface"""
        style = ttk.Style()
        style.theme_use('clam')  # Tema base
        
        # Cores
        bg_color = "#1C2027"
        fg_color = "#FFFFFF"
        accent_color = "#3C78D8"
        
        # Configura o fundo da janela principal
        self.root.configure(bg=bg_color)
        
        # Configura estilos de widgets
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TButton", background=accent_color, foreground=fg_color, 
                       font=("Segoe UI", 10, "bold"), padding=5)
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background=bg_color, foreground=fg_color)
        style.configure("TListbox", background="#2C313A", foreground=fg_color, 
                       font=("Segoe UI", 10), borderwidth=0)
        
        # Configura hover para botões
        style.map("TButton",
                 background=[("active", "#2A5699"), ("pressed", "#1E3D6B")],
                 foreground=[("active", fg_color), ("pressed", fg_color)])
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"+{x}+{y}")
    
    def load_profiles(self):
        """Carrega os perfis disponíveis"""
        profiles = []
        profiles_dir = cloud_quest_root / "profiles"
        
        try:
            if not profiles_dir.exists():
                write_log(f"Diretório de perfis não encontrado: {profiles_dir}", "Warning")
                return profiles
            
            # Lista todos os arquivos JSON no diretório de perfis
            for file_path in profiles_dir.glob("*.json"):
                try:
                    profile_name = file_path.stem  # Nome do arquivo sem extensão
                    
                    # Tenta ler o arquivo para extrair detalhes do perfil
                    with open(file_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        
                    # Extrai o nome do jogo, se disponível
                    game_name = profile_data.get("GameName", "Jogo desconhecido")
                    
                    profiles.append({
                        "name": profile_name,
                        "game_name": game_name,
                        "file_path": str(file_path)
                    })
                    
                except Exception as e:
                    write_log(f"Erro ao ler perfil {file_path}: {str(e)}", "Error")
            
            # Ordena perfis por nome do jogo
            profiles.sort(key=lambda x: x["game_name"])
            
        except Exception as e:
            write_log(f"Erro ao carregar perfis: {str(e)}", "Error")
        
        return profiles
    
    def build_interface(self):
        """Constrói a interface do usuário"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = ttk.Label(main_frame, text="Selecione um Perfil", style="Title.TLabel")
        title_label.pack(pady=(0, 15))
        
        # Lista de perfis
        profiles_frame = ttk.Frame(main_frame)
        profiles_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.profiles_listbox = tk.Listbox(profiles_frame, bg="#2C313A", fg="#FFFFFF",
                                          font=("Segoe UI", 10), selectbackground="#3C78D8",
                                          selectforeground="#FFFFFF", borderwidth=1,
                                          relief=tk.SOLID, highlightthickness=0)
        self.profiles_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar para a lista
        scrollbar = ttk.Scrollbar(profiles_frame, orient=tk.VERTICAL, 
                                 command=self.profiles_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_listbox.config(yscrollcommand=scrollbar.set)
        
        # Popula a lista de perfis
        if self.profiles:
            for profile in self.profiles:
                self.profiles_listbox.insert(tk.END, f"{profile['game_name']} ({profile['name']})")
            # Seleciona o primeiro por padrão
            self.profiles_listbox.selection_set(0)
        else:
            self.profiles_listbox.insert(tk.END, "Nenhum perfil encontrado")
            self.profiles_listbox.config(state=tk.DISABLED)
        
        # Botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        launch_button = ttk.Button(buttons_frame, text="Iniciar", command=self.launch_selected)
        launch_button.pack(side=tk.RIGHT, padx=5)
        
        exit_button = ttk.Button(buttons_frame, text="Sair", command=self.root.destroy)
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Vincula duplo clique na lista para iniciar
        self.profiles_listbox.bind("<Double-1>", lambda event: self.launch_selected())
        
        # Configuração final
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.after(100, lambda: self.root.focus_force())  # Garante o foco
    
    def launch_selected(self):
        """Inicia o CloudQuest com o perfil selecionado"""
        if not self.profiles:  # Sem perfis disponíveis
            self.root.destroy()
            return
        
        selected_idx = self.profiles_listbox.curselection()
        if not selected_idx:  # Nada selecionado
            return
        
        profile = self.profiles[selected_idx[0]]
        self.save_selected_profile(profile["name"])
        self.root.destroy()
    
    def save_selected_profile(self, profile_name):
        """Salva o perfil selecionado no arquivo temporário"""
        try:
            temp_file = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")
            with open(temp_file, 'w') as f:
                f.write(profile_name)
            
            write_log(f"Perfil selecionado e salvo: {profile_name}", "Info")
        except Exception as e:
            write_log(f"Erro ao salvar perfil selecionado: {str(e)}", "Error")
    
    def run(self):
        """Inicia o loop principal da interface"""
        self.root.mainloop()

def select_profile():
    """Executa o seletor de perfil e retorna o nome do perfil selecionado"""
    selector = ProfileSelector()
    selector.run()
    
    # O perfil já foi salvo pelo seletor, apenas retornamos para continuar o fluxo
    temp_file = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")
    try:
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                profile_name = f.read().strip()
                if profile_name:
                    return profile_name
    except Exception as e:
        write_log(f"Erro ao ler perfil selecionado: {str(e)}", "Error")
    
    return None