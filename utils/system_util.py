"""
系统信息工具模块

提供获取服务器系统信息的函数，包括操作系统、Python版本、上传限制等。
"""

import platform
import sys
import os


# Layui 版本号常量
LAYUI_VERSION = '2.13.3'


def get_python_version() -> str:
    """
    获取 Python 版本信息

    :return: Python 版本字符串，如 "3.10.11"
    """
    return platform.python_version()


def get_os_info() -> str:
    """
    获取操作系统信息

    :return: 操作系统名称，如 "Linux" 或 "Windows-10"
    """
    os_name = platform.system()
    return os_name


def get_upload_max_filesize() -> str:
    """
    获取上传文件大小限制

    :return: 上传大小限制字符串，如 "50M / 1024M"
    """
    # 从环境变量获取单个文件和总上传限制
    single_file_limit = os.getenv('UPLOAD_MAX_FILESIZE', '50M')
    total_limit = os.getenv('UPLOAD_TOTAL_SIZE', '1024M')

    return f"{single_file_limit} / {total_limit}"


def get_max_execution_time() -> str:
    """
    获取最大执行时间限制

    :return: 执行时间限制字符串，如 "6000秒"
    """
    max_time = os.getenv('MAX_EXECUTION_TIME', '6000')
    return f"{max_time}秒"


def get_framework_version() -> str:
    """
    获取 Web 框架版本

    :return: 框架版本字符串，如 "FastAPI 0.104.1"
    """
    try:
        import fastapi
        version = getattr(fastapi, '__version__', 'unknown')
        return f"FastAPI {version}"
    except ImportError:
        pass

    try:
        import flask
        version = getattr(flask, '__version__', 'unknown')
        return f"Flask {version}"
    except ImportError:
        pass

    return "未知框架"


def get_system_info() -> dict:
    """
    获取服务器系统信息

    :return: 包含所有系统信息的字典
    """
    return {
        'os': get_os_info(),
        'python': get_python_version(),
        'upload_max_filesize': get_upload_max_filesize(),
        'max_execution_time': get_max_execution_time(),
        'framework': get_framework_version(),
        'layui_version': LAYUI_VERSION,
    }
