import os
import uuid
from datetime import datetime
from fastapi import UploadFile
from typing import Tuple

# 文件存储配置（可放到配置文件中）
UPLOAD_DIR = "./uploads/tender_attachments"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf", "docx", "doc", "xlsx", "xls", "zip", "rar"}

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否合法"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_ext(filename: str) -> str:
    """获取文件扩展名（小写）"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_file_path(project_tender_id: int, filename: str) -> Tuple[str, str]:
    """
    生成文件存储路径
    :param project_tender_id: 投标ID
    :param filename: 原始文件名
    :return: 相对路径、绝对路径
    """
    # 创建日期目录
    date_dir = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(UPLOAD_DIR, str(project_tender_id), date_dir)
    os.makedirs(save_dir, exist_ok=True)

    # 生成唯一文件名（避免重复）
    file_ext = get_file_ext(filename)
    unique_filename = f"{uuid.uuid4()}.{file_ext}" if file_ext else str(uuid.uuid4())

    # 相对路径（存储到数据库）和绝对路径（实际存储）
    relative_path = os.path.join(str(project_tender_id), date_dir, unique_filename)
    absolute_path = os.path.join(save_dir, unique_filename)

    return relative_path, absolute_path

async def save_upload_file(file: UploadFile, file_path: str) -> int:
    """
    保存上传的文件到指定路径
    :param file: 上传的文件对象
    :param file_path: 存储绝对路径
    :return: 文件大小（字节）
    """
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 按1MB分块读取
            f.write(chunk)
            file_size += len(chunk)
    return file_size