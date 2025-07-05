import PyInstaller.__main__
import os
import shutil
import sys
from PyQt5.QtCore import QLibraryInfo

# 清理之前的构建
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# 获取Qt安装路径
qt_path = QLibraryInfo.location(QLibraryInfo.PrefixPath)

# 定义打包参数
params = [
    "main.py",  # 替换为你的脚本文件名
    "--name=OnlineReading",
    "--onefile",
    "--windowed",
    "--icon=icon.ico",
    "--splash=loading.png",
    "--clean",
    "--noconfirm",
    "--add-binary=" + os.path.join(qt_path, "bin", "Qt5WebEngineCore.dll;PyQt5/Qt/bin"),
    "--add-binary="
    + os.path.join(qt_path, "bin", "Qt5WebEngineWidgets.dll;PyQt5/Qt/bin"),
    "--add-binary=" + os.path.join(qt_path, "bin", "Qt5WebEngine.dll;PyQt5/Qt/bin"),
    "--add-binary="
    + os.path.join(qt_path, "bin", "QtWebEngineProcess.exe;PyQt5/Qt/bin"),
    "--add-data=" + os.path.join(qt_path, "resources") + ";PyQt5/Qt/resources",
    "--add-data="
    + os.path.join(qt_path, "translations", "qtwebengine_locales")
    + ";PyQt5/Qt/translations/qtwebengine_locales",
    "--hidden-import=PyQt5.QtWebEngineWidgets",
    "--hidden-import=PyQt5.QtWebEngineCore",
    "--hidden-import=PyQt5.QtWebEngineProcess",
]

# 添加所有必要的资源文件
webengine_resources = [
    "qtwebengine_resources.pak",
    "qtwebengine_devtools_resources.pak",
    "qtwebengine_resources_100p.pak",
    "qtwebengine_resources_200p.pak",
    "icudtl.dat",
]

for resource in webengine_resources:
    src = os.path.join(qt_path, "resources", resource)
    if os.path.exists(src):
        params.append(f"--add-data={src};PyQt5/Qt/resources")

# 添加平台插件
params.append(
    "--add-data="
    + os.path.join(qt_path, "plugins", "platforms")
    + ";PyQt5/Qt/plugins/platforms"
)

# 执行打包
PyInstaller.__main__.run(params)

print("打包完成！EXE文件位于 dist 目录中")
