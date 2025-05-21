# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/mallor/Documentos/GitHub/CloudQuest/assets/icons/app_icon.ico', 'assets/icons/'), ('/home/mallor/Documentos/GitHub/CloudQuest/CloudQuest', 'CloudQuest'), ('/home/mallor/Documentos/GitHub/CloudQuest/QuestConfig', 'QuestConfig'), ('/home/mallor/Documentos/GitHub/CloudQuest/logs', 'logs')],
    hiddenimports=['configparser', 'io', 'os', 'sys', 're', 'json', 'datetime', 'pathlib', 'logging', 'subprocess', 'time', 'shutil', 'tempfile', 'platform', 'glob', 'socket', 'webbrowser', 'zipfile', 'base64', 'urllib', 'urllib.request', 'urllib.parse', 'threading', 'queue', 'signal', 'uuid', 'traceback', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.simpledialog', 'tkinter.constants', 'tkinter.font', '_tkinter', 'CloudQuest', 'CloudQuest.main', 'CloudQuest.core', 'CloudQuest.utils', 'CloudQuest.config', 'QuestConfig', 'QuestConfig.ui.app', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.ImageDraw', 'PIL.ImageFont', 'psutil', 'requests', 'watchdog', 'watchdog.events', 'watchdog.observers', 'win32com', 'win32gui', 'win32con', 'win32api', 'win32process', 'win32service', 'win32serviceutil', 'winshell', 'CloudQuest.__init__', 'CloudQuest.main', 'CloudQuest.config.__init__', 'CloudQuest.config.settings', 'CloudQuest.core.__init__', 'CloudQuest.core.game_launcher', 'CloudQuest.core.notification_ui', 'CloudQuest.core.profile_manager', 'CloudQuest.core.sync_manager', 'CloudQuest.utils.__init__', 'CloudQuest.utils.logger', 'CloudQuest.utils.paths', 'CloudQuest.utils.rclone', 'QuestConfig.__init__', 'QuestConfig.__main__', 'QuestConfig.core.__init__', 'QuestConfig.core.config', 'QuestConfig.core.game', 'QuestConfig.interfaces.services', 'QuestConfig.services.__init__', 'QuestConfig.services.pcgamingwiki', 'QuestConfig.services.save', 'QuestConfig.services.shortcut', 'QuestConfig.services.steam', 'QuestConfig.ui.__init__', 'QuestConfig.ui.app', 'QuestConfig.ui.views', 'QuestConfig.utils.__init__', 'QuestConfig.utils.logger', 'QuestConfig.utils.paths', 'QuestConfig.utils.text_utils'],
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
    a.binaries,
    a.datas,
    [],
    name='CloudQuest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/home/mallor/Documentos/GitHub/CloudQuest/assets/icons/app_icon.ico'],
)
