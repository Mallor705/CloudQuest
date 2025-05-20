# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Adicionar todos os arquivos de código-fonte do CloudQuest e QuestConfig
cloudquest_files = [
    ("C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\CloudQuest", "CloudQuest")
]

questconfig_files = [
    ("C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\QuestConfig", "QuestConfig")
]

# Recursos adicionais
extra_files = [
    ("C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\assets\icons", "assets/icons"),
    ("C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\config\profiles", "config/profiles"),
    ("C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\logs", "logs")
]

a = Analysis(['app.py'],
             pathex=[r'C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest'],
             binaries=[],
             datas=cloudquest_files + questconfig_files + extra_files,
             hiddenimports=[
                 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
                 'PIL', 'PIL.Image', 'PIL.ImageTk', 'psutil', 'json', 'subprocess',
                 'CloudQuest', 'CloudQuest.main', 'QuestConfig', 'QuestConfig.ui.app'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
             
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='CloudQuest',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True ,icon=r'C:\Users\messi\OneDrive - MSFT\Documentos\GitHub\CloudQuest\assets\icons\app_icon.ico' )
          
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='CloudQuest')
