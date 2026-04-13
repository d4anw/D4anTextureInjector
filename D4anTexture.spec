# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for D4an Texture Injector
# Texture replacement tool for Stumble Guys game

a = Analysis(
    ['D4anTexture.py'],
    pathex=[],
    binaries=[],
    datas=[('background.png', '.'), ('Textures', 'Textures')],
    hiddenimports=['urllib', 'urllib.request', 'urllib.error', 'json', 'threading', 'subprocess'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'wx', 'PIL',
        'setuptools', 'pip', 'wheel', 'pkg_resources', 'distutils',
        'test', 'unittest', 'doctest', 'pydoc', 'ctypes', 'socket',
        'asyncio', 'multiprocessing', 'ssl'
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='D4anTexture',
    debug=False,
    bootloader_ignore_signals=True,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    manifest='manifest.xml',
)

