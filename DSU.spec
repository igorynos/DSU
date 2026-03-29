# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DSU (Device Setup Utility)
Компиляция: pyinstaller DSU.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect customtkinter assets
customtkinter_datas = collect_data_files('customtkinter')

# Additional data files
added_files = [
    ('go-firmware/firmware.exe', 'go-firmware'),  # Windows
    ('go-firmware/firmware', 'go-firmware'),      # Linux/Mac
    ('README.md', '.'),
]

# Hidden imports
hidden_imports = [
    'tkinter',
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
] + collect_submodules('customtkinter')

a = Analysis(
    ['app_modern.py'],
    pathex=[],
    binaries=[],
    datas=added_files + customtkinter_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DSU',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if sys.platform == 'win32' else None,
    version='version_info.txt' if sys.platform == 'win32' else None,
)
