import sys
from PyQt6.QtWidgets import QApplication
from doctalk.main_window import MainWindow
import asyncio
import qasync

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # 设置任务栏图标
    app.setWindowIcon(window.windowIcon())
    
    # 直接使用 exec() 而不是异步等待
    return app.exec()

if __name__ == "__main__":
    try:
        # 直接运行，不使用 asyncio
        sys.exit(main())
    except KeyboardInterrupt:
        pass