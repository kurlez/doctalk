from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QProgressBar, QPushButton, QLineEdit,
                           QFileDialog)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent
import os
import platform
import asyncio

# 添加处理文件的工作线程
class ProcessThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, files, output_dir, voice):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.voice = voice

    def run(self):
        try:
            from doctalk.doctalk import process_files
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # 在新的事件循环中运行异步函数
            loop.run_until_complete(process_files(self.files, self.output_dir, self.voice))
            loop.close()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class DropArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = parent
        
        layout = QVBoxLayout()
        
        # 根据操作系统设置默认输出目录
        default_dir = self.get_default_output_dir()
        
        # 添加输出目录选择部分
        dir_layout = QHBoxLayout()
        
        self.dir_label = QLabel("输出目录:")
        dir_layout.addWidget(self.dir_label)
        
        self.dir_edit = QLineEdit(default_dir)
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)
        
        self.dir_button = QPushButton("选择")
        self.dir_button.clicked.connect(self.choose_directory)
        self.dir_button.setFixedWidth(60)
        dir_layout.addWidget(self.dir_button)
        
        layout.addLayout(dir_layout)
        
        # 拖放提示标签
        self.label = QLabel("将文件拖放到这里\n支持 .md 和 .epub 文件")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
    def get_default_output_dir(self):
        """根据操作系统返回默认输出目录"""
        if platform.system() == 'Windows':
            return "D:\\Downloads\\DToutput"
        else:
            return os.path.expanduser("~/Downloads/DToutput")

    def normalize_path(self, path):
        """根据操作系统规范化路径显示"""
        if platform.system() == 'Windows':
            return path.replace('/', '\\')
        else:
            return path.replace('\\', '/')

    def choose_directory(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.dir_edit.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            # 规范化路径显示
            normalized_path = self.normalize_path(dir_path)
            self.dir_edit.setText(normalized_path)
            # 确保目录存在
            os.makedirs(normalized_path, exist_ok=True)
    
    def get_output_directory(self):
        """获取当前选择的输出目录"""
        return self.dir_edit.text()
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.md', '.epub')):
                    event.acceptProposedAction()
                    return
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.md', '.epub')):
                files.append(file_path)
        
        if files:
            self.main_window.process_files(files)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.process_thread = None
        
    def initUI(self):
        self.setWindowTitle('DocTalk')
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        # 增加窗口高度以适应新添加的控件
        self.setFixedSize(QSize(300, 250))
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        
        # 添加标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("DocTalk")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        min_button = QPushButton("-")
        min_button.clicked.connect(self.showMinimized)
        min_button.setFixedSize(20, 20)
        
        close_button = QPushButton("×")
        close_button.clicked.connect(self.close)
        close_button.setFixedSize(20, 20)
        
        title_layout.addWidget(min_button)
        title_layout.addWidget(close_button)
        
        layout.addLayout(title_layout)
        
        # 添加拖放区域
        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 10px;
            }
            QLabel {
                color: #666666;
                font-size: 14px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666666;
            }
            QPushButton:hover {
                color: #000000;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QPushButton#dirButton {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QPushButton#dirButton:hover {
                background-color: #d0d0d0;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def process_files(self, files):
        """处理拖放的文件"""
        self.drop_area.label.setText("正在处理...")
        self.drop_area.progress.show()
        
        # 使用选择的输出目录
        output_dir = self.drop_area.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建并启动处理线程
        self.process_thread = ProcessThread(files, output_dir, "xiaoxiao")
        self.process_thread.finished.connect(self.on_process_finished)
        self.process_thread.error.connect(self.on_process_error)
        self.process_thread.start()

    def on_process_finished(self):
        self.drop_area.label.setText("处理完成！\n将文件拖放到这里")
        self.drop_area.progress.hide()

    def on_process_error(self, error_msg):
        self.drop_area.label.setText(f"处理失败：{error_msg}\n将文件拖放到这里")
        self.drop_area.progress.hide()