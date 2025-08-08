# -*- mode: python ; coding: utf-8 -*-

# NetMule PyInstaller Spec File - Optimierte Version

block_cipher = None

# Nur die wichtigsten Hidden Imports
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'networkx',
    'networkx.readwrite.json_graph',
    'pandas',
    'openpyxl',
    'python_gedcom_2.parser',
    'email',
    'jaraco.text',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    'numpy._pytesttester',
    'numpy.testing',
    'pandas.plotting',
    'pandas.io.html',
    'pandas.io.parquet',
    'pandas.io.sql',
    'networkx.generators',
    'networkx.algorithms.centrality',
    'networkx.algorithms.community',
    'networkx.algorithms.flow',
    'networkx.algorithms.isomorphism',
    'networkx.drawing'  # Hinzugefügt, um den Fehler zu beheben
]

# Module, die definitiv ausgeschlossen werden
excludes = [
    # PyQt5 - nicht benötigte Module
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore', 
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebKit',
    'PyQt5.QtWebKitWidgets',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtSql',
    'PyQt5.QtTest',
    'PyQt5.QtXml',
    'PyQt5.QtNetwork',
    'PyQt5.QtMultimedia',
    'PyQt5.QtOpenGL',
    'PyQt5.QtBluetooth',
    'PyQt5.QtNfc',
    
    # Pandas - nicht benötigte Module
    'pandas.tests',
    
    # Wissenschaftliche Libraries
    'matplotlib',
    'scipy',
    'numpy.testing',
    
    # Development/Testing
    'pytest',
    'unittest',
    'IPython',
    'jupyter',
    'pip',
    
    # Andere GUI Frameworks
    'tkinter',
    'turtle',
    
    # Nicht benötigte Standard Libraries
    'sqlite3',
]

a = Analysis(
    ['NetMule.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=['.'],  # Für benutzerdefinierte Hooks
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Test-Module entfernen, um Größe zu reduzieren (vorübergehend deaktiviert für Debugging)
# def remove_from_list(input_list, item_name):
#     return [item for item in input_list if item_name.lower() not in item[0].lower()]
# a.pure = remove_from_list(a.pure, 'test')
# a.pure = remove_from_list(a.pure, 'tests')
# a.pure = remove_from_list(a.pure, 'testing')
# a.pure = remove_from_list(a.pure, 'example')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetMule',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['qtcore.dll', 'qtwidgets.dll', 'qtgui.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)