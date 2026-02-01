# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# 跨平台配置
platform = sys.platform
icon_file = None

if platform == 'win32':
    icon_file = 'icon.ico'
elif platform == 'darwin':  # macOS
    icon_file = 'icon.icns'
else:  # Linux
    icon_file = 'icon.png'

# 检查图标文件是否存在
if icon_file and not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.png', '.'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'caldav',
    ],
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
    name='Nextcloud_task_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=platform == 'darwin',  # macOS 需要启用
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS 专用：创建 .app 包
if platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Nextcloud_task_client.app',
        icon=icon_file,
        bundle_identifier='com.nextcloud.taskclient',
        info_plist={
            'CFBundleName': 'Nextcloud Task Client',
            'CFBundleDisplayName': 'Nextcloud Task Client',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
