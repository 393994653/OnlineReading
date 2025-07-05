import datetime
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
    QSequentialAnimationGroup,
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
    QProgressBar,
    QGraphicsOpacityEffect,
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
    QLinearGradient,
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
        print(f"JS Console: {message} at line {lineNumber}")
        pass


class Win11TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 保存父窗口引用
        self.is_maximized = False  # 跟踪窗口最大化状态
        self.animating = False  # 跟踪动画状态
        self.button_effects = {}  # 存储按钮的透明度效果

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
            }
        """
        )
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

        # 设置标题栏样式 - 移除backdrop-filter属性
        self.setStyleSheet(
            """
            Win11TitleBar {
                background-color: rgba(255, 255, 255, 0.9);  /* 调整不透明度替代模糊效果 */
                border-bottom: 1px solid rgba(220, 220, 220, 0.8);
                border-radius: 8px 8px 0 0;  /* 添加顶部圆角 */
            }
        """
        )

        # 初始化导航按钮状态（初始不可用）
        self.update_nav_buttons_state(False, False)

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
                border-radius: 4px;  /* 圆角按钮 */
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            #navButton:hover {
                background-color: rgba(0, 0, 0, 0.08);  /* 轻微高亮 */
            }
            #navButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);  /* 按下效果 */
            }
            #navButton:disabled {
                color: #a0a0a0;  /* 禁用状态颜色 */
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
                border-radius: 4px;  /* 圆角按钮 */
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }
            #titleButton:hover {
                background-color: rgba(0, 0, 0, 0.08);  /* 轻微高亮 */
            }
            #titleButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);  /* 按下效果 */
            }
            #titleButton:last-child:hover {  /* 关闭按钮特殊处理 */
                background-color: #e81123;  /* Win11 关闭按钮hover颜色 */
                color: white;
            }
            #titleButton:last-child:pressed {
                background-color: #c41021;  /* 关闭按钮按下颜色 */
            }
        """
        )
        btn.setFocusPolicy(Qt.NoFocus)  # 移除焦点框
        return btn

    def update_nav_buttons_state(self, can_go_back, can_go_forward):
        """更新导航按钮状态"""
        self.back_btn.setEnabled(can_go_back)
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


class MinimalBrowser(QWidget):
    def __init__(self, target_url):
        super().__init__()
        self.target_url = target_url
        self.is_fullscreen = False  # 跟踪全屏状态
        self.last_mouse_position = QPoint()  # 记录鼠标位置
        self.title_bar_visible = False  # 标题栏是否可见
        self.is_refreshing = False  # 刷新状态标记
        self.normal_geometry = None  # 保存窗口正常状态的几何信息

        # 添加标题栏显示延迟计时器
        self.title_bar_timer = QTimer(self)
        self.title_bar_timer.setSingleShot(True)  # 只触发一次
        self.title_bar_timer.timeout.connect(self.show_title_bar_after_delay)
        self.hover_delay = 1000  # 悬停延迟时间1000毫秒（1秒）

        # 记录鼠标是否在顶部区域
        self.mouse_in_top_area = False

        # 设置窗口无边框和透明背景
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

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

        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                background: transparent;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 1.5px;
            }
        """
        )
        self.progress_bar.hide()
        self.content_layout.addWidget(self.progress_bar)

        # 修改用户数据目录处理 - 确保使用正确的持久化路径
        # 获取正确的持久化路径
        if getattr(sys, "frozen", False):
            # 打包模式：使用用户的应用数据目录
            base_dir = os.path.join(
                os.getenv("APPDATA") or os.path.expanduser("~"), "OnlineReading"
            )
        else:
            # 开发模式：使用当前工作目录
            base_dir = os.getcwd()
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        # 创建用户数据目录
        self.profile_path = os.path.join(base_dir, "browser_profile")
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)

        # 创建配置文件 - 确保使用绝对路径
        self.profile = QWebEngineProfile("CustomProfile", self)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )
        self.profile.setPersistentStoragePath(self.profile_path)
        self.profile.setCachePath(os.path.join(self.profile_path, "cache"))
        print(f"持久化存储路径: {self.profile.persistentStoragePath()}")
        print(f"缓存路径: {self.profile.cachePath()}")

        # 设置语言首选项为中文
        self.profile.setHttpAcceptLanguage("zh-CN,zh;q=0.9,en;q=0.8")

        # 创建自定义页面
        self.page = CustomWebEnginePage(self.profile, self)

        # 创建浏览器视图
        self.browser = QWebEngineView(self)
        self.browser.setPage(self.page)
        self.content_layout.addWidget(self.browser)

        # 创建标题栏 - 作为浮动组件而不是布局的一部分
        self.title_bar = Win11TitleBar(self)
        self.title_bar.setParent(self.content_frame)  # 设置父对象为内容框架
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

        # 连接进度变化事件
        self.browser.loadProgress.connect(self.update_progress)

        # 使用定时器更新导航按钮状态（替代缺失的信号）
        self.nav_timer = QTimer(self)
        self.nav_timer.timeout.connect(self.update_nav_buttons)
        self.nav_timer.start(500)  # 每500ms检查一次

        # 鼠标移动检测定时器
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        self.mouse_timer.start(100)  # 每100毫秒检查一次

        # 窗口圆角动画
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # 创建右下角大小拖拽手柄
        self.size_grip = QSizeGrip(self)  # 只创建一个右下角的缩放手柄

        # 确保标题栏初始位置正确
        QTimer.singleShot(100, self.position_title_bar)

    def position_title_bar(self):
        """定位标题栏到内容框架顶部"""
        if self.content_frame:
            # 标题栏的父对象是content_frame，所以设置位置为(0,0)即可
            self.title_bar.setGeometry(
                0, 0, self.content_frame.width(), self.title_bar.height()
            )

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
                width: 6px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: rgba(150, 150, 150, 0.5);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(100, 100, 100, 0.7);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        )

    def update_window_title(self, title):
        self.title_bar.title.setText(title)
        self.setWindowTitle(title)

    def update_progress(self, progress):
        """更新进度条状态"""
        if progress < 100:
            self.progress_bar.setValue(progress)
            self.progress_bar.show()
        else:
            # 加载完成后延迟隐藏进度条
            QTimer.singleShot(500, self.progress_bar.hide)

    def on_load_finished(self, success):
        self.unlock_refresh()
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
            """
            )
            # 页面加载完成后注入自定义JavaScript
            self.inject_custom_js()
        else:
            # 页面加载失败时显示错误信息
            self.browser.setHtml(
                """
                <html>
                    <head>
                        <style>
                            body {
                                font-family: 'Segoe UI', sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                background: #f8f9fa;
                                color: #495057;
                            }
                            .error-container {
                                text-align: center;
                                max-width: 500px;
                                padding: 2rem;
                                border-radius: 8px;
                                background: white;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                            }
                            h1 {
                                color: #e03131;
                                margin-bottom: 1rem;
                            }
                            p {
                                margin-bottom: 1.5rem;
                                line-height: 1.6;
                            }
                            .btn {
                                background: #4dabf7;
                                color: white;
                                border: none;
                                padding: 0.75rem 1.5rem;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 1rem;
                                transition: background 0.2s;
                            }
                            .btn:hover {
                                background: #339af0;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="error-container">
                            <h1>页面加载失败</h1>
                            <p>无法加载请求的页面。请检查您的网络连接或稍后再试。</p>
                            <button class="btn" onclick="window.location.reload()">重新加载</button>
                        </div>
                    </body>
                </html>
            """
            )

    def inject_custom_js(self):
        """注入自定义JavaScript"""
        hide_scrollbar_js = """
            // 保留滚动功能但隐藏滚动条
            document.documentElement.style.overflow = 'auto';
            document.documentElement.style.scrollbarWidth = 'thin';
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
                    width: 6px;
                    height: 6px;
                }
                ::-webkit-scrollbar-track {
                    background: transparent;
                }
                ::-webkit-scrollbar-thumb {
                    background: rgba(150, 150, 150, 0.5);
                    border-radius: 3px;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: rgba(100, 100, 100, 0.7);
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
            # 保存当前窗口状态以便恢复
            self.normal_geometry = self.geometry()
            # 隐藏标题栏和进度条
            self.title_bar.hide()
            self.title_bar_visible = False
            self.progress_bar.hide()
            self.showFullScreen()
            # 隐藏大小调整手柄
            self.size_grip.hide()
            # 执行JavaScript全屏
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
            # 恢复窗口状态
            self.setGeometry(self.normal_geometry)
            # 恢复UI元素
            self.title_bar.show()
            self.title_bar_visible = True
            self.size_grip.show()
            self.showNormal()
            # 退出JavaScript全屏
            self.page.runJavaScript(
                """
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                }
            """
            )

    def check_mouse_position(self):
        """检查鼠标位置，决定是否显示标题栏"""
        if self.is_fullscreen:
            return

        current_pos = QCursor.pos()
        window_pos = self.mapFromGlobal(current_pos)
        self.last_mouse_position = current_pos

        # 检查鼠标是否在顶部区域（40像素内）
        in_top_area = window_pos.y() < 40

        if in_top_area and not self.title_bar_visible:
            # 鼠标进入顶部区域，启动延迟显示定时器
            if not self.title_bar_timer.isActive():
                self.title_bar_timer.start(self.hover_delay)
        elif not in_top_area and self.title_bar_visible:
            # 鼠标离开顶部区域，立即隐藏标题栏
            self.title_bar.hide()
            self.title_bar_visible = False
            # 如果定时器在运行，停止定时器
            if self.title_bar_timer.isActive():
                self.title_bar_timer.stop()

    def show_title_bar_after_delay(self):
        """延迟显示标题栏（1秒后）"""
        current_pos = QCursor.pos()
        window_pos = self.mapFromGlobal(current_pos)

        # 再次检查鼠标是否仍在顶部区域
        if window_pos.y() < 20 and not self.title_bar_visible:
            self.title_bar.show()
            self.title_bar_visible = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 更新标题栏位置和大小
        self.position_title_bar()

        # 定位右下角大小拖拽手柄
        size = 16
        self.size_grip.setGeometry(
            self.width() - size, self.height() - size, size, size
        )

    def update_nav_buttons(self):
        """更新导航按钮状态"""
        can_go_back = self.browser.history().canGoBack()
        can_go_forward = self.browser.history().canGoForward()
        self.title_bar.update_nav_buttons_state(can_go_back, can_go_forward)

    def go_back(self):
        """导航回上一页"""
        if self.browser.history().canGoBack():
            self.browser.back()

    def go_forward(self):
        """导航到下一页"""
        if self.browser.history().canGoForward():
            self.browser.forward()

    def reload_page(self):
        """刷新当前页面 - 添加防抖和锁定机制"""
        # 如果正在刷新，则忽略请求
        if self.is_refreshing:
            return

        # 设置刷新锁定
        self.is_refreshing = True

        # 禁用刷新按钮
        self.title_bar.refresh_btn.setEnabled(False)

        # 停止当前加载（如果有）
        self.browser.stop()

        # 执行刷新
        self.browser.reload()

        # 2秒后解除锁定（防止连续刷新）
        QTimer.singleShot(2000, self.unlock_refresh)

    def unlock_refresh(self):
        """解除刷新锁定"""
        self.is_refreshing = False

        # 启用刷新按钮
        self.title_bar.refresh_btn.setEnabled(True)

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
            if not self.is_refreshing:
                self.reload_page()
        # Ctrl+R刷新页面
        elif event.key() == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            if not self.is_refreshing:
                self.reload_page()
        # Ctrl+加号放大
        elif event.key() == Qt.Key_Plus and event.modifiers() == Qt.ControlModifier:
            self.browser.setZoomFactor(self.browser.zoomFactor() + 0.1)
        # Ctrl+减号缩小
        elif event.key() == Qt.Key_Minus and event.modifiers() == Qt.ControlModifier:
            self.browser.setZoomFactor(max(0.5, self.browser.zoomFactor() - 0.1))
        # Ctrl+0重置缩放
        elif event.key() == Qt.Key_0 and event.modifiers() == Qt.ControlModifier:
            self.browser.setZoomFactor(1.0)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        # 确保所有数据写入磁盘
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies
        )

        # 停止加载并清理页面
        self.browser.stop()

        # 断开页面与视图的连接
        self.browser.setPage(None)
        self.page = None

        # 清理配置文件
        self.profile.deleteLater()

        # 延迟关闭以确保资源释放
        def final_close():
            # 确保所有WebEngine进程终止
            QApplication.quit()

        QTimer.singleShot(500, final_close)
        event.ignore()


# 设置日志记录
logging.basicConfig(
    filename="browser_error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def log_exception(exctype, value, tb):
    """记录未捕获的异常"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))

    # 确定日志文件路径
    if getattr(sys, "frozen", False):
        log_dir = os.path.join(
            os.getenv("APPDATA") or os.path.expanduser("~"), "OnlineReading"
        )
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "browser_error.log")
    else:
        log_path = "browser_error.log"

    # 记录错误
    with open(log_path, "a") as log_file:
        log_file.write(f"{datetime.datetime.now()} - Uncaught exception: {error_msg}\n")

    # 同时输出到控制台（如果可用）
    sys.__excepthook__(exctype, value, tb)


def set_webengine_environment():
    """设置WebEngine所需的环境变量"""
    if getattr(sys, "frozen", False):
        # 打包后模式
        base_path = sys._MEIPASS

        # 设置所有必要的WebEngine环境变量
        os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.join(
            base_path, "PyQt5", "Qt", "bin", "QtWebEngineProcess.exe"
        )

        # 添加资源文件路径
        resources_path = os.path.join(base_path, "PyQt5", "Qt", "resources")
        os.environ["QTWEBENGINE_RESOURCES_PATH"] = resources_path

        # 添加本地化文件路径
        locales_path = os.path.join(base_path, "PyQt5", "Qt", "translations")
        os.environ["QTWEBENGINE_LOCALES_PATH"] = locales_path

        # 添加额外的Chromium标志
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu"
    else:
        # 开发模式
        from PyQt5.QtCore import QLibraryInfo

        os.environ["QTWEBENGINEPROCESS_PATH"] = os.path.join(
            QLibraryInfo.location(QLibraryInfo.BinariesPath), "QtWebEngineProcess.exe"
        )


if __name__ == "__main__":
    try:
        import pyi_splash

        pyi_splash.close()
    except ImportError:
        pass

    sys.excepthook = log_exception
    set_webengine_environment()

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
