# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['BehaveTestRunner.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('features', 'features'),
        ('config.env', '.'),
        ('generate_report.py', '.'),
        ('chromedriver.exe', '.'),
    ],
    hiddenimports=['selenium.webdriver.chrome.webdriver', 'selenium.webdriver.common.service', 'selenium.webdriver.remote.webdriver', 'behave', 'behave.runner', 'behave.configuration'],
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
    name='BehaveTestRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
