import logging
import sys
import os
import traceback
from PyQt5.QtCore import (
    QUrl,
    Qt,
    QTimer,
    QPoint,
    QSize,
    QRect,
    QPropertyAnimation,
    QEasingCurve,
    QByteArray,
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QSizeGrip,
    QFrame,
    QStyle,
    QStyleOption,
    QStylePainter,
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView,
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
)
from PyQt5.QtGui import (
    QIcon,
    QCursor,
    QPainter,
    QPainterPath,
    QRegion,
    QColor,
    QPalette,
    QFontDatabase,
    QPixmap,
    QFont,
    QKeySequence,
)
from PyQt5.QtSvg import QSvgWidget

# 解决链接在新窗口打开的问题
class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)

    def acceptNavigationRequest(self, url, type, isMainFrame):
        # 强制所有导航请求在当前页面打开
        return True

    def createWindow(self, type):
        # 返回当前页面实例，确保所有链接在当前页面打开
        return self

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 重写此方法以捕获JavaScript控制台消息
        # print(f"JS Console: {message} at line {lineNumber}")
        pass


class Win11TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 保存父窗口引用
        self.is_maximized = False  # 跟踪窗口最大化状态

        # 设置标题栏高度（Win11 标题栏标准高度）
        self.setFixedHeight(32)

        # 创建主布局（水平布局）
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(8, 0, 8, 0)  # 调整边距以容纳新按钮
        self.main_layout.setSpacing(4)  # 按钮间距

        # 创建导航按钮（前进、后退）
        self.back_btn = self.create_nav_button("←")  # 后退按钮
        self.forward_btn = self.create_nav_button("→")  # 前进按钮
        # 添加刷新按钮
        self.refresh_btn = self.create_nav_button("↻")  # 刷新按钮

        # 添加导航按钮到布局
        self.main_layout.addWidget(self.back_btn)
        self.main_layout.addWidget(self.forward_btn)
        self.main_layout.addWidget(self.refresh_btn)  # 添加刷新按钮

        # 窗口标题标签（调整样式使其与导航按钮对齐）
        self.title = QLabel("OnlineReading")
        self.title.setObjectName("titleLabel")
        self.title.setStyleSheet(
            """
            #titleLabel {
                color: #1a1a1a;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
                padding: 0 8px;
                background-color: transparent;
                border-radius: 4px;
            }
            Win11TitleBar {
                background-color: transparent;
                border: none;
            }
        """
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 允许透明背景
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.main_layout.addWidget(self.title)

        # 添加伸缩项，将窗口控制按钮推到右侧
        self.main_layout.addStretch(1)

        # 创建窗口控制按钮
        self.min_btn = self.create_title_button("\u2013")  # 最小化
        self.max_btn = self.create_title_button("\u25a1")  # 最大化
        self.close_btn = self.create_title_button("\u00d7")  # 关闭

        # 添加窗口控制按钮到布局
        self.main_layout.addWidget(self.min_btn)
        self.main_layout.addWidget(self.max_btn)
        self.main_layout.addWidget(self.close_btn)

        # 连接按钮信号
        self.back_btn.clicked.connect(self.parent.go_back)  # 后退功能
        self.forward_btn.clicked.connect(self.parent.go_forward)  # 前进功能
        self.refresh_btn.clicked.connect(self.parent.reload_page)  # 刷新功能
        self.min_btn.clicked.connect(self.parent.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)

        # 设置标题栏样式为透明
        self.setStyleSheet(
            """
            Win11TitleBar {
                background-color: transparent;
                border: none;
            }
        """
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 允许透明背景

        # 初始化导航按钮状态（初始不可用）
        self.update_nav_buttons_state()

        # 定时更新导航按钮状态（检查是否可前进/后退）
        self.nav_timer = QTimer(self)
        self.nav_timer.timeout.connect(self.update_nav_buttons_state)
        self.nav_timer.start(500)  # 每500ms检查一次

        # 初始隐藏标题栏（鼠标移动到顶部时才显示）
        self.hide()

    def create_nav_button(self, text):
        """创建导航按钮（前进/后退/刷新）"""
        btn = QPushButton(text)
        btn.setObjectName("navButton")
        btn.setFixedSize(32, 28)  # 比窗口控制按钮稍小
        btn.setStyleSheet(
            """
            #navButton {
                color: #1a1a1a;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            #navButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
            }
            #navButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
            #navButton:disabled {
                color: #a0a0a0;
            }
        """
        )
        btn.setFocusPolicy(Qt.NoFocus)  # 移除焦点框
        # 只有前进后退按钮初始禁用，刷新按钮始终可用
        if text in ["←", "→"]:
            btn.setEnabled(False)
        return btn

    def create_title_button(self, text):
        """创建符合 Win11 风格的标题栏按钮（最小化/最大化/关闭）"""
        btn = QPushButton(text)
        btn.setObjectName("titleButton")
        btn.setFixedSize(46, 28)  # Win11 标题栏按钮标准大小
        btn.setStyleSheet(
            """
            #titleButton {
                color: #1a1a1a;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            #titleButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
            }
            #titleButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
            #titleButton:last-child:hover {
                background-color: #e81123;
                color: white;
            }
            #titleButton:last-child:pressed {
                background-color: #c41021;
            }
        """
        )
        btn.setFocusPolicy(Qt.NoFocus)  # 移除焦点框
        return btn

    def update_nav_buttons_state(self):
        """更新导航按钮状态（根据浏览历史判断是否可前进/后退）"""
        if hasattr(self.parent, "browser") and self.parent.browser:
            # 检查是否可以后退
            can_go_back = self.parent.browser.history().canGoBack()
            self.back_btn.setEnabled(can_go_back)

            # 检查是否可以前进
            can_go_forward = self.parent.browser.history().canGoForward()
            self.forward_btn.setEnabled(can_go_forward)

    def mouseDoubleClickEvent(self, event):
        """双击标题栏切换最大化状态"""
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()

    def toggle_maximize(self):
        """切换窗口最大化/还原状态"""
        if self.is_maximized:
            # 还原窗口
            self.parent.showNormal()
            self.is_maximized = False
            self.max_btn.setText("\u25a1")  # 恢复方框图标
        else:
            # 最大化窗口
            self.parent.showMaximized()
            self.is_maximized = True
            self.max_btn.setText("\u2398")  # 切换为还原图标

    def mousePressEvent(self, event):
        """支持拖动窗口（标题栏区域）"""
        if event.button() == Qt.LeftButton:
            self.parent.drag_start_position = (
                event.globalPos() - self.parent.frameGeometry().topLeft()
            )
            event.accept()

    def enterEvent(self, event):
        """鼠标进入标题栏时显示按钮"""
        self.back_btn.show()
        self.forward_btn.show()
        self.refresh_btn.show()  # 显示刷新按钮
        self.min_btn.show()
        self.max_btn.show()
        self.close_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开标题栏且不在窗口顶部时隐藏按钮"""
        if not self.parent.is_fullscreen and self.parent.last_mouse_position.y() > 20:
            self.back_btn.hide()
            self.forward_btn.hide()
            self.refresh_btn.hide()  # 隐藏刷新按钮
            self.min_btn.hide()
            self.max_btn.hide()
            self.close_btn.hide()
        super().leaveEvent(event)


class MinimalBrowser(QWidget):
    def __init__(self, target_url):
        super().__init__()
        self.target_url = target_url
        self.is_fullscreen = False  # 跟踪全屏状态


        # 添加标题栏显示延迟计时器
        self.title_bar_timer = QTimer(self)
        self.title_bar_timer.setSingleShot(True)  # 只触发一次
        self.title_bar_timer.timeout.connect(self.show_title_bar_after_delay)
        self.hover_delay = 800  # 悬停延迟时间（毫秒），可调整

        # 记录鼠标是否在顶部区域
        self.mouse_in_top_area = False

        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowIcon(self.get_icon("icon.png"))

        # 设置窗口大小
        self.resize(1200, 800)
        self.setWindowTitle("OnlineReading")

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建圆角内容框架
        self.content_frame = QFrame(self)
        self.content_frame.setObjectName("contentFrame")
        self.content_frame.setStyleSheet(
            """
            #contentFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """
        )
        self.main_layout.addWidget(self.content_frame)

        # 创建内容布局
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # 创建用户数据目录
        self.profile_path = os.path.join(os.getcwd(), "browser_profile")
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)

        # 创建配置文件
        self.profile = QWebEngineProfile("CustomProfile", self)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(self.profile_path)
        self.profile.setCachePath(os.path.join(self.profile_path, "cache"))

        # 设置语言首选项为中文
        self.profile.setHttpAcceptLanguage("zh-CN,zh;q=0.9,en;q=0.8")

        # 创建自定义页面
        self.page = CustomWebEnginePage(self.profile, self)

        # 创建浏览器视图
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        self.content_layout.addWidget(self.browser)

        # 创建标题栏（覆盖在浏览器上方）
        self.title_bar = Win11TitleBar(self)
        self.title_bar.setParent(self.content_frame)
        self.title_bar.raise_()  # 确保标题栏在最上层
        self.title_bar.hide()  # 初始隐藏

        # 配置浏览器设置
        self.configure_browser()

        # 加载目标网址
        self.browser.load(QUrl(self.target_url))

        # 连接加载完成信号
        self.browser.loadFinished.connect(self.on_load_finished)

        # 设置窗口标题变化事件
        self.browser.titleChanged.connect(self.update_window_title)

        # 鼠标移动检测定时器
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        self.mouse_timer.start(100)  # 每100毫秒检查一次

        # 记录鼠标位置
        self.last_mouse_position = QPoint()

        # 窗口圆角动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # 创建右下角大小拖拽手柄（只保留这一个）
        self.size_grip = QSizeGrip(self)
        self.size_grip.setStyleSheet("background-color: transparent;")  # 透明背景
        self.size_grip.raise_()  # 确保在最上层

    def get_icon(self, filename):
        """获取图标，支持开发环境和打包后环境"""
        # 尝试从当前目录加载
        base_path = os.path.dirname(os.path.abspath(__file__))
        local_path = os.path.join(base_path, filename)
        
        # 如果文件存在，直接使用
        if os.path.exists(local_path):
            return QIcon(local_path)
        
        # 如果是在打包后的环境中运行
        if hasattr(sys, '_MEIPASS'):
            # 尝试从 MEIPASS 目录加载
            meipass_path = os.path.join(sys._MEIPASS, filename)
            if os.path.exists(meipass_path):
                return QIcon(meipass_path)
            
            # 尝试从 MEIPASS 下的资源目录加载
            resource_path = os.path.join(sys._MEIPASS, "resources", filename)
            if os.path.exists(resource_path):
                return QIcon(resource_path)
        
        # 如果都没有找到，返回空图标（避免崩溃）
        return QIcon()

    def configure_browser(self):
        """配置浏览器设置"""
        settings = self.browser.settings()

        # 启用所有必要功能
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)

        # 隐藏滚动条但保留滚动功能
        self.browser.setStyleSheet(
            """
            QWebEngineView {
                border: none;
            }
            QScrollBar:vertical {
                width: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
            QScrollBar::handle:vertical {
                width: 0px;
            }
            QScrollBar::handle:horizontal {
                height: 0px;
            }
        """
        )

        # 注入CSS隐藏网页滚动条但保留滚动功能
        hide_scrollbar_js = """
            // 保留滚动功能但隐藏滚动条
            document.documentElement.style.overflow = 'auto';
            document.documentElement.style.scrollbarWidth = 'none';
            document.documentElement.style.msOverflowStyle = 'none';
            
            // 防止在新窗口打开链接
            document.addEventListener('click', function(event) {
                var target = event.target;
                while (target && target.tagName !== 'A') {
                    target = target.parentNode;
                }
                if (target && target.tagName === 'A' && target.target === '_blank') {
                    target.target = '_self';
                    event.preventDefault();
                    window.location.href = target.href;
                }
            });
            
            // 隐藏滚动条
            var style = document.createElement('style');
            style.innerHTML = `
                ::-webkit-scrollbar {
                    width: 0px;
                    height: 0px;
                }
                ::-webkit-scrollbar-track {
                    background: transparent;
                }
                ::-webkit-scrollbar-thumb {
                    background: transparent;
                }
            `;
            document.head.appendChild(style);
            
            // 监听全屏请求
            document.addEventListener('fullscreenchange', function(event) {
                if (document.fullscreenElement) {
                    window.external.notify('enterFullscreen');
                } else {
                    window.external.notify('exitFullscreen');
                }
            });
            
            document.addEventListener('webkitfullscreenchange', function(event) {
                if (document.webkitFullscreenElement) {
                    window.external.notify('enterFullscreen');
                } else {
                    window.external.notify('exitFullscreen');
                }
            });
        """
        self.page.runJavaScript(hide_scrollbar_js)

        # 注册用于全屏通信的通道
        # self.page.registerChannel("fullscreen", self)

    def update_window_title(self, title):
        self.title_bar.title.setText(title)
        self.setWindowTitle(title)

    def on_load_finished(self, success):
        if success:
            # 设置中文语言环境
            self.browser.page().runJavaScript(
                """
                if (navigator.language) {
                    document.documentElement.lang = 'zh-CN';
                }
                // 尝试设置语言为中文
                if (document.querySelector('html')) {
                    document.querySelector('html').lang = 'zh-CN';
                }
                
                // 隐藏滚动条但保留滚动功能
                document.documentElement.style.scrollbarWidth = 'none';
                document.documentElement.style.msOverflowStyle = 'none';
                
                // 防止在新窗口打开链接
                document.addEventListener('click', function(event) {
                    var target = event.target;
                    while (target && target.tagName !== 'A') {
                        target = target.parentNode;
                    }
                    if (target && target.tagName === 'A' && target.target === '_blank') {
                        target.target = '_self';
                        event.preventDefault();
                        window.location.href = target.href;
                    }
                });
                
                // 添加样式隐藏滚动条
                var style = document.createElement('style');
                style.innerHTML = `
                    ::-webkit-scrollbar {
                        width: 0px;
                        height: 0px;
                    }
                    ::-webkit-scrollbar-track {
                        background: transparent;
                    }
                    ::-webkit-scrollbar-thumb {
                        background: transparent;
                    }
                `;
                document.head.appendChild(style);
                
                // 监听全屏请求
                document.addEventListener('fullscreenchange', function(event) {
                    if (document.fullscreenElement) {
                        window.external.notify('enterFullscreen');
                    } else {
                        window.external.notify('exitFullscreen');
                    }
                });
                
                document.addEventListener('webkitfullscreenchange', function(event) {
                    if (document.webkitFullscreenElement) {
                        window.external.notify('enterFullscreen');
                    } else {
                        window.external.notify('exitFullscreen');
                    }
                });
            """
            )
        else:
            pass

        # 连接全屏请求信号
        self.page.fullScreenRequested.connect(self.handle_fullscreen_request)

    def handle_fullscreen_request(self, request):
        """处理HTML5全屏API请求"""
        if request.toggleOn():
            # 进入全屏模式
            self.enter_fullscreen()
        else:
            # 退出全屏模式
            self.exit_fullscreen()
        request.accept()

    def enter_fullscreen(self):
        """进入全屏模式"""
        if not self.is_fullscreen:
            self.is_fullscreen = True
            self.title_bar.hide()
            self.size_grip.hide()  # 隐藏拖拽手柄
            self.showFullScreen()
            # 通知页面已进入全屏
            self.page.runJavaScript(
                """
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(err => {
                        console.error('Fullscreen request error:', err);
                    });
                }
            """
            )

    def exit_fullscreen(self):
        """退出全屏模式"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.title_bar.show()
            self.size_grip.show()  # 显示拖拽手柄
            self.showNormal()
            # 通知页面已退出全屏
            self.page.runJavaScript(
                """
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                }
            """
            )

    def check_mouse_position(self):
        """检查鼠标位置，决定是否延迟显示标题栏"""
        if self.is_fullscreen:
            return

        current_pos = QCursor.pos()
        window_pos = self.mapFromGlobal(current_pos)
        self.last_mouse_position = current_pos

        # 检查鼠标是否在顶部区域（40像素内）
        if window_pos.y() < 40:
            if not self.mouse_in_top_area:
                self.mouse_in_top_area = True
                self.title_bar_timer.start(self.hover_delay)  # 延迟指定毫秒后显示
        else:
            if self.mouse_in_top_area:
                self.mouse_in_top_area = False
                self.title_bar_timer.stop()
                self.title_bar.hide()

    def show_title_bar_after_delay(self):
        """延迟后显示标题栏"""
        if self.mouse_in_top_area:  # 确保鼠标仍在顶部区域
            self.title_bar.show()
            self.title_bar.raise_()  # 确保标题栏在最上层

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 更新标题栏位置和大小
        self.title_bar.setGeometry(0, 0, self.content_frame.width(), 32)
        
        # 定位右下角大小拖拽手柄
        size = 16
        if not self.is_fullscreen:  # 只在非全屏模式下显示
            self.size_grip.setGeometry(
                self.width() - size, self.height() - size, size, size
            )
            self.size_grip.raise_()  # 确保在最上层
        else:
            self.size_grip.hide()

    def go_back(self):
        """导航回上一页"""
        if self.browser.history().canGoBack():
            self.browser.back()

    def go_forward(self):
        """导航到下一页"""
        if self.browser.history().canGoForward():
            self.browser.forward()

    def reload_page(self):
        """刷新当前页面"""
        self.browser.reload()

    # 窗口拖动功能
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 40:
            self.drag_start_position = (
                event.globalPos() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, "drag_start_position"):
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, "drag_start_position"):
            del self.drag_start_position
            event.accept()

    def keyPressEvent(self, event):
        """处理快捷键"""
        # ESC键退出全屏
        if event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.exit_fullscreen()
        # F5键刷新页面
        elif event.key() == Qt.Key_F5:
            self.reload_page()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 确保所有数据写入磁盘
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(self.profile_path)
        super().closeEvent(event)


# 设置日志记录
logging.basicConfig(
    filename="browser_error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def log_exception(exctype, value, tb):
    """记录未捕获的异常"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    logging.error(f"Uncaught exception: {error_msg}")
    sys.__excepthook__(exctype, value, tb)


if __name__ == "__main__":
    sys.excepthook = log_exception

    # 目标网址
    TARGET_URL = "http://zhenghao.x3322.net:38083"

    app = QApplication(sys.argv)

    # 设置应用名称
    app.setApplicationName("OnlineReading")

    # 设置应用样式为系统原生样式
    app.setStyle("Fusion")

    # 设置应用调色板为浅色模式
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(30, 30, 30))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(30, 30, 30))
    palette.setColor(QPalette.Text, QColor(30, 30, 30))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(30, 30, 30))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # 创建浏览器窗口
    browser = MinimalBrowser(TARGET_URL)
    browser.show()

    sys.exit(app.exec_())