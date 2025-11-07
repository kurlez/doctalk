__version__ = '0.4.0'

import os
from datetime import datetime
from pathlib import Path

def get_version():
    """获取版本号"""
    return __version__

def get_build_time():
    """获取构建时间"""
    # 首先尝试从环境变量获取（在构建时设置）
    build_time = os.environ.get('DOCTALK_BUILD_TIME')
    if build_time:
        return build_time
    
    # 如果没有环境变量，尝试从包的安装时间获取
    try:
        # 获取包的安装时间（通过检查 __init__.py 文件的修改时间）
        package_path = Path(__file__).parent
        init_file = package_path / '__init__.py'
        if init_file.exists():
            mtime = init_file.stat().st_mtime
            build_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            return build_time
    except Exception:
        pass
    
    # 如果都获取不到，返回当前时间
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
