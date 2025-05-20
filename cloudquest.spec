# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\assets\\icons\\app_icon.ico', 'assets/icons/'), ('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\assets\\icons\\*.ico', 'assets/icons'), ('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\assets\\icons\\*.png', 'assets/icons'), ('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\CloudQuest', 'CloudQuest'), ('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\QuestConfig', 'QuestConfig'), ('C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\logs', 'logs')],
    hiddenimports=['configparser', 'io', 'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'logging', 'subprocess', 'time', 'shutil', 'tempfile', 'platform', 'glob', 'socket', 'webbrowser', 'zipfile', 'base64', 'urllib', 'urllib.request', 'urllib.parse', 'threading', 'queue', 'signal', 'uuid', 'traceback', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.simpledialog', 'tkinter.constants', 'tkinter.font', '_tkinter', 'CloudQuest', 'CloudQuest.main', 'CloudQuest.core', 'CloudQuest.utils', 'CloudQuest.config', 'QuestConfig', 'QuestConfig.ui.app', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont', 'psutil', 'requests', 'watchdog', 'watchdog.events', 'watchdog.observers', 'win32com', 'win32gui', 'win32con', 'win32api', 'win32process', 'win32service', 'win32serviceutil', 'CloudQuest.main', 'CloudQuest.__init__', 'CloudQuest.config.settings', 'CloudQuest.config.__init__', 'CloudQuest.core.game_launcher', 'CloudQuest.core.notification_ui', 'CloudQuest.core.profile_manager', 'CloudQuest.core.sync_manager', 'CloudQuest.core.__init__', 'CloudQuest.utils.logger', 'CloudQuest.utils.paths', 'CloudQuest.utils.rclone', 'CloudQuest.utils.__init__', 'QuestConfig.__init__', 'QuestConfig.__main__', 'QuestConfig.core.config', 'QuestConfig.core.game', 'QuestConfig.core.__init__', 'QuestConfig.interfaces.services', 'QuestConfig.services.pcgamingwiki', 'QuestConfig.services.save', 'QuestConfig.services.shortcut', 'QuestConfig.services.steam', 'QuestConfig.services.__init__', 'QuestConfig.ui.app', 'QuestConfig.ui.views', 'QuestConfig.ui.__init__', 'QuestConfig.utils.logger', 'QuestConfig.utils.paths', 'QuestConfig.utils.text_utils', 'QuestConfig.utils.__init__'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CloudQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\messi\\OneDrive - MSFT\\Documentos\\GitHub\\CloudQuest\\assets\\icons\\app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CloudQuest',
)
