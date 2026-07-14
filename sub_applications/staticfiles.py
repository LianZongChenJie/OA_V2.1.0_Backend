from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config.env import UploadConfig


def mount_staticfiles(app: FastAPI) -> None:
    """
    挂载静态文件
    """
    app.mount(f'{UploadConfig.UPLOAD_PREFIX}', StaticFiles(directory=f'{UploadConfig.UPLOAD_PATH}'), name='profile')
    # 挂载简历知识库前端页面
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    if os.path.isdir(static_dir):
        app.mount('/static', StaticFiles(directory=static_dir, html=True), name='static')
