# build.py - PyInstaller 打包脚本
import os
import sys
import PyInstaller.__main__

# 主程序文件名
main_script = 'main.py'

# 图标文件（确保此文件存在）
icon_file = 'icon.ico'
window_icon = 'icon.png'

# 打包输出目录
build_dir = 'dist'

# 隐藏控制台窗口（启用 Windows 子系统）
console_option = '--noconsole'

# 打包选项列表
options = [
    main_script,                # 主脚本文件
    '--name', 'OnlineReading',  # 可执行文件名称
    '--icon', icon_file,        # 应用图标
    '--distpath', build_dir,    # 输出目录
    '--workpath', 'build',      # 临时构建目录
    '--specpath', 'spec',       # spec 文件目录
    console_option,             # 控制台选项
    '--onefile',                # 打包为单个可执行文件
    '--windowed',               # 窗口应用（无控制台）
    
    '--add-data', f'{window_icon}{os.pathsep}resources',

    # 包含 Qt WebEngine 核心文件
    '--collect-data', 'PyQt5.QtWebEngineCore',
    
    # 包含 Qt WebEngine 资源文件
    '--collect-data', 'PyQt5.QtWebEngineWidgets',
    
    # 包含 Qt WebEngine 翻译文件
    '--collect-data', 'PyQt5.QtWebEngineProcess',
    
    # 包含 Qt WebEngine 核心资源
    '--collect-data', 'PyQt5.QtWebEngineCore.qtwebengine_resources',
    
    # 包含 Qt WebEngine 核心翻译
    '--collect-data', 'PyQt5.QtWebEngineCore.qtwebengine_locales',
    
    # 包含 Qt WebEngine 进程
    '--collect-binaries', 'PyQt5.QtWebEngineProcess',
    
    # 清理构建目录
    '--clean',
    
    # 隐藏 PyInstaller 输出
    '--noconfirm'
]

def main():
    # 检查图标文件是否存在
    if not os.path.exists(icon_file):
        print(f"错误: 图标文件 '{icon_file}' 不存在")
        print("请创建一个 128x128 像素的 .ico 文件并命名为 'icon.ico'")
        print("您可以使用在线工具将 PNG 转换为 ICO 格式")
        return

    if not os.path.exists(window_icon):
        print(f"错误: 图标文件 '{window_icon}' 不存在")
    
    # 检查主脚本文件是否存在
    if not os.path.exists(main_script):
        print(f"错误: 主脚本文件 '{main_script}' 不存在")
        print("请确保您的浏览器程序保存为 'main.py'")
        return
    
    print("开始打包 OnlineReading 浏览器应用...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 运行 PyInstaller
        PyInstaller.__main__.run(options)
        
        print("\n打包成功完成！")
        print(f"可执行文件位于: {os.path.abspath(build_dir)}")
        print("注意: 首次运行时可能需要几秒钟初始化")
        
    except Exception as e:
        print(f"\n打包过程中出错: {str(e)}")
        print("可能的解决方案:")
        print("1. 确保安装了所有依赖: pip install PyQt5 PyQtWebEngine pyinstaller")
        print("2. 确保您有足够的磁盘空间")
        print("3. 尝试关闭防病毒软件")
        print("4. 查看 PyInstaller 文档: https://pyinstaller.org/en/stable/")

if __name__ == '__main__':
    main()