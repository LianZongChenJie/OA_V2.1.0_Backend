from datetime import datetime
from typing import Optional


def format_timestamp(timestamp: int, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    格式化时间戳（支持秒级和毫秒级）

    Args:
        timestamp: 时间戳（秒级或毫秒级）
        format_str: 格式化字符串

    Returns:
        格式化后的时间字符串
    """
    if not timestamp or timestamp == 0:
        return None

    try:
        # 自动识别毫秒级时间戳（大于 10^12 的视为毫秒级）
        if timestamp > 9999999999:
            timestamp = timestamp / 1000
        
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(format_str)
    except (OSError, ValueError, OverflowError):
        return None


def format_date(timestamp: int, format_str: str = "%Y-%m-%d") -> Optional[str]:
    """格式化日期（只显示年月日）"""
    return format_timestamp(timestamp, format_str)


def now_timestamp() -> int:
    """获取当前时间戳（秒级）"""
    return int(datetime.now().timestamp())

def int_time(str_time: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> int:
    try:
        if len(str_time) != 19:
            """
            时间格式不为 2026-04-15 01:22:33形式时更改时间格式
            """
            format_str = "%Y-%m-%d"
        dt = datetime.strptime(str_time, format_str)
        return int(dt.timestamp())
    except Exception as e:
        print(e)
        return 0