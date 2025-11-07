import sys
import os
from PyQt6.QtWidgets import QApplication
from doctalk.gui.main_window import MainWindow
import asyncio
import qasync

# 在 macOS 上，这个警告是由系统日志（os_log）直接输出的，无法在 Python 代码中完全抑制
# 这是一个已知的 macOS + PyQt 系统级警告，完全无害，不影响功能
# 如果需要隐藏它，可以在终端运行时使用：doctalk-gui 2>/dev/null
# 或者设置环境变量：export OS_ACTIVITY_MODE=disable
if sys.platform == 'darwin':
    # 设置环境变量来减少 Qt 调试信息
    os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false')
    os.environ.setdefault('QT_FATAL_WARNINGS', '0')
    # 尝试抑制 macOS 系统日志（可能不完全有效，因为警告是通过 os_log 直接输出的）
    if 'OS_ACTIVITY_MODE' not in os.environ:
        os.environ['OS_ACTIVITY_MODE'] = 'disable'

class FilterStderr:
    """过滤 macOS mach port 错误消息和其他系统警告"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.filtered_messages = [
            'error messaging the mach port for IMKCFRunLoopWakeUpReliable',
            'IMKCFRunLoopWakeUpReliable',
            'mach port',
        ]
    
    def write(self, message):
        # 过滤掉特定的警告消息（不区分大小写）
        message_lower = message.lower()
        if any(filter_msg.lower() in message_lower for filter_msg in self.filtered_messages):
            return  # 忽略这个消息
        self.original_stderr.write(message)
    
    def flush(self):
        self.original_stderr.flush()
    
    def fileno(self):
        return self.original_stderr.fileno()
    
    def __getattr__(self, name):
        return getattr(self.original_stderr, name)

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # 设置任务栏图标
    app.setWindowIcon(window.windowIcon())
    
    # 直接使用 exec() 而不是异步等待
    return app.exec()

if __name__ == "__main__":
    # 在 macOS 上，需要在最早的时候设置环境变量和过滤器
    if sys.platform == 'darwin':
        # 保存原始 stderr
        original_stderr = sys.stderr
        
        # 创建过滤器并替换 stderr
        filtered_stderr = FilterStderr(original_stderr)
        sys.stderr = filtered_stderr
        
        try:
            sys.exit(main())
        except KeyboardInterrupt:
            pass
        finally:
            # 恢复原始 stderr
            sys.stderr = original_stderr
    else:
        try:
            sys.exit(main())
        except KeyboardInterrupt:
            pass