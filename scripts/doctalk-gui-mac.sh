#!/bin/bash
# macOS 启动脚本 - 抑制 mach port 警告
# 
# 使用方法：
#   ./scripts/doctalk-gui-mac.sh
#   或者
#   doctalk-gui 2>/dev/null

# 设置环境变量来抑制 macOS 系统日志
export OS_ACTIVITY_MODE=disable
export QT_LOGGING_RULES="*.debug=false"
export QT_FATAL_WARNINGS=0

# 运行 GUI，将 stderr 重定向到 /dev/null 来隐藏警告
# 注意：这也会隐藏其他可能的错误信息
python3 -m doctalk.gui 2>/dev/null
