# -*- mode: python ; coding: utf-8 -*-
"""
NEUROSITY MONITOR - SPEC FILE PYINSTALLER
Configuration optimisée pour Flask + SocketIO + Multiprocessing
Génère un .exe qui ouvre automatiquement le navigateur
"""

import sys
import os
from datetime import datetime
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ============================================
# CONFIGURATION DE BASE
# ============================================

block_cipher = None

# Nom daté (jour_mois_année) pour distinguer les builds entre eux.
# build.bat le transmet via APP_NAME ; sinon on prend la date du jour.
app_name = os.environ.get('APP_NAME') or datetime.now().strftime('%d_%m_%y') + '_NeurosityMonitor'

# ============================================
# DONNÉES À COLLECTER
# ============================================

# Neurosity SDK - collecter tous les sous-modules
neurosity_hiddenimports = collect_submodules('neurosity')

# Flask et extensions
flask_hiddenimports = [
    'flask',
    'flask_socketio',
    'flask.json',
    'flask.helpers',
    'jinja2',
    'jinja2.ext',
    'werkzeug',
    'werkzeug.routing',
    'werkzeug.security',
    'click',
]

# SocketIO et dépendances
socketio_hiddenimports = [
    'socketio',
    'engineio',
    'engineio.async_drivers.threading',
    'simple_websocket',
    'wsproto',
]

# Cryptographie
crypto_hiddenimports = [
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
]

# Data science
data_hiddenimports = [
    'pandas',
    'numpy',
    'statistics',
]

# Environnement
env_hiddenimports = [
    'dotenv',
    'python-dotenv',
]

# Autres
other_hiddenimports = [
    'queue',
    'multiprocessing',
    'multiprocessing.spawn',
    'multiprocessing.queues',
    'threading',
    'webbrowser',
    'tempfile',
    'socket',
    'csv',
    'json',
    'pathlib',
    'datetime',
    'logging',
    'logging.handlers',
]

# Combiner tous les imports cachés
all_hiddenimports = (
    neurosity_hiddenimports +
    flask_hiddenimports +
    socketio_hiddenimports +
    crypto_hiddenimports +
    data_hiddenimports +
    env_hiddenimports +
    other_hiddenimports
)

# ============================================
# FICHIERS DE DONNÉES
# ============================================

# Templates Flask
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

# Collecter les données de Flask
try:
    flask_datas = collect_data_files('flask_socketio')
    datas.extend(flask_datas)
except:
    pass

# Collecter les données de Jinja2
try:
    jinja_datas = collect_data_files('jinja2')
    datas.extend(jinja_datas)
except:
    pass

# ============================================
# BINAIRES ADDITIONNELS
# ============================================

binaries = []

# ============================================
# ANALYSE
# ============================================

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'PIL',
        'tkinter',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================
# PYZ - Archive Python
# ============================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================
# EXE - Exécutable
# ============================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Pas de console visible
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajoutez 'icon.ico' si vous avez une icône
)

# ============================================
# COLLECT - Collecter tous les fichiers
# ============================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# ============================================
# CONFIGURATION MULTIPROCESSING
# ============================================

# Important pour multiprocessing avec PyInstaller
# Les imports doivent être disponibles au runtime
a.pure += [
    ('neurosity_worker', 'neurosity_worker.py', 'PYMODULE'),
    ('data_manager', 'data_manager.py', 'PYMODULE'),
]

print("\n" + "="*60)
print("CONFIGURATION PYINSTALLER - NEUROSITY MONITOR")
print("="*60)
print(f"Application: {app_name}")
print(f"Hidden imports: {len(all_hiddenimports)}")
print(f"Data files: {len(datas)}")
print(f"Console: False (pas de console)")
print("Mode: One-directory (dist/{}/...".format(app_name))
print("="*60 + "\n")
