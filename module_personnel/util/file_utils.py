import os
from datetime import datetime
from fastapi import UploadFile
import uuid
import hashlib
# 创建目录
def make_dir(file_path):
    return os.makedirs(file_path, exist_ok=True)

# 生成日期相关的文件目录
def generate_file_path(base_dir: str):
    """
    生成日期相关的文件目录
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    file_path = os.path.join(base_dir, timestamp)
    make_dir(file_path)
    return file_path


def generate_file_name(file_name: str) -> str:
    """
    生成文件名
    """
    file_ext = os.path.splitext(file_name)[1][1:]  # 去掉文件名的扩展名前面的点
    return f"{uuid.uuid4()}.{file_ext}"

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

async def generate_md5(fileName: str)->str:
    """
    生成文件的MD5值
    """
    with open(fileName, 'rb') as f:
        md5obj = hashlib.md5()
        while chunk := f.read(8192):
            md5obj.update(chunk)
    return md5obj.hexdigest()

async def generate_sha1(fileName: str)->str:
    """
    生成文件的SHA1值
    """
    with open(fileName, 'rb') as f:
        sha1obj = hashlib.sha1()
        while chunk := f.read(8192):
            sha1obj.update(chunk)
    return sha1obj.hexdigest()

async def delete_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print("删除文件失败", e)
