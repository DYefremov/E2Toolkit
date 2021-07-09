import os
import datetime
import distutils.util

EXE_NAME = 'run.py'
DIR_PATH = os.getcwd()
COMPILING_PLATFORM = distutils.util.get_platform()
PATH_EXE = [os.path.join(DIR_PATH, EXE_NAME)]
STRIP = True
BUILD_DATE = datetime.datetime.now().strftime("%y%m%d")

block_cipher = None

excludes = ['app.streams.mpv',
            'gi.repository.Gst',
            'gi.repository.GstBase',
            'gi.repository.GstVideo',
            'youtube_dl',
            'tkinter']

ui_files = []

a = Analysis([EXE_NAME],
             pathex=PATH_EXE,
             binaries=None,
             datas=ui_files,
             hiddenimports=['fileinput', 'uuid'],
             hookspath=[],
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='E2Toolkit',
          debug=False,
          strip=STRIP,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=STRIP,
               upx=True,
               name='E2Toolkit')

app = BUNDLE(coll,
             name='E2Toolkit.app',
             icon='icon.icns',
             bundle_identifier=None,
             info_plist={
                 'NSPrincipalClass': 'NSApplication',
                 'CFBundleName': 'E2Toolkit',
                 'CFBundleDisplayName': 'E2Toolkit',
                 'LSApplicationCategoryType': 'public.app-category.utilities',
                 'LSMinimumSystemVersion': '10.13',
                 'CFBundleShortVersionString': "1.0.0.{} Pre-Alpha".format(BUILD_DATE),
                 'NSHumanReadableCopyright': u"Copyright © 2021, Dmitriy Yefremov",
                 'NSRequiresAquaSystemAppearance': 'false'
             })
