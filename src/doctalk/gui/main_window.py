from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QProgressBar, QPushButton, QLineEdit,
                           QFileDialog, QTableWidget, QTableWidgetItem)
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
    file_status = pyqtSignal(str, str)  # (file_path, status)

    def __init__(self, files, output_dir, voice):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.voice = voice

    def run(self):
        """
        Run the file processing in a separate thread with proper event loop handling.
        On macOS, using asyncio.run() for each file avoids mach port conflicts.
        """
        try:
            # 延迟导入以避免UI线程加载时间
            from doctalk.doctalk import process_single_file
            
            # 在macOS上，为每个文件使用独立的 asyncio.run() 调用
            # 这样可以避免事件循环冲突和 mach port 错误
            for file_path in self.files:
                try:
                    self.file_status.emit(file_path, "processing")
                    # 使用 asyncio.run() 为每个文件创建独立、干净的事件循环
                    # 这避免了在macOS上出现 mach port 错误
                    asyncio.run(
                        process_single_file(file_path, self.output_dir, self.voice)
                    )
                    self.file_status.emit(file_path, "processed")
                except Exception as e:
                    error_msg = str(e)
                    self.file_status.emit(file_path, f"error: {error_msg}")
                    # 继续处理其他文件
                    print(f"Error processing {file_path}: {error_msg}")
            
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
        self.file_row_map = {}
        
    def initUI(self):
        self.setWindowTitle('DocTalk')
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        # 增加窗口尺寸以适应文件列表
        self.setFixedSize(QSize(420, 420))
        
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

        # 文件状态表格
        self.file_table = QTableWidget(0, 2)
        self.file_table.setHorizontalHeaderLabels(["文件", "状态"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setEditTriggers(self.file_table.EditTrigger.NoEditTriggers)
        self.file_table.setSelectionBehavior(self.file_table.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(self.file_table.SelectionMode.NoSelection)
        layout.addWidget(self.file_table)
        
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
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 3px;
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
        
        # 初始化文件列表为未开始
        self._init_file_status_list(files)

        # 创建并启动处理线程
        self.process_thread = ProcessThread(files, output_dir, "xiaoxiao")
        self.process_thread.finished.connect(self.on_process_finished)
        self.process_thread.error.connect(self.on_process_error)
        self.process_thread.file_status.connect(self.on_file_status_update)
        self.process_thread.start()

    def on_process_finished(self):
        self.drop_area.label.setText("处理完成！\n将文件拖放到这里")
        self.drop_area.progress.hide()

    def on_process_error(self, error_msg):
        self.drop_area.label.setText(f"处理失败：{error_msg}\n将文件拖放到这里")
        self.drop_area.progress.hide()

    def _init_file_status_list(self, files):
        """清空并初始化文件状态列表为 未开始"""
        self.file_table.setRowCount(0)
        self.file_row_map.clear()
        for file_path in files:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            file_item = QTableWidgetItem(os.path.basename(file_path))
            status_item = QTableWidgetItem("未开始")
            self.file_table.setItem(row, 0, file_item)
            self.file_table.setItem(row, 1, status_item)
            self.file_row_map[file_path] = row

    def on_file_status_update(self, file_path: str, status: str):
        """更新指定文件的状态单元格"""
        row = self.file_row_map.get(file_path)
        if row is None:
            # 可能来自重复拖入，追加一行
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            self.file_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
            self.file_row_map[file_path] = row
        # 规范化状态展示
        status_map = {
            "not started": "未开始",
            "processing": "处理中",
            "processed": "已完成",
        }
        display_status = status_map.get(status.lower(), status)
        self.file_table.setItem(row, 1, QTableWidgetItem(display_status))