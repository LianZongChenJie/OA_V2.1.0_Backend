import os

from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from common.aspect.pre_auth import CurrentUserDependency

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from typing import List
from module_personnel.service.file_service import FileService
from module_personnel.entity.vo.file_vo import OaFileBaseModel
from utils.response_util import ResponseUtil

file_controller = APIRouterPro(
    prefix='/common/file', order_num=3, tags=['人事管理-员工档案-文件'], dependencies=[PreAuthDependency()]
)

@file_controller.post(
    "/upload/multiple",
    summary='上传多个文件',
    description='用于上传多个文件',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:file:upload')],
)

async def upload_file(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    files: List[UploadFile] = File(..., description="多个文件"),
) -> Response:
    admin_id = current_user.user.user_id
    result = await FileService.add_file(files, query_db, admin_id)
    return ResponseUtil.success(data=result)

@file_controller.put(
    "/rename",
    summary='文件重命名',
    description='用于更新文件名称',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:file:update')],
)
async def rename_file(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaFileBaseModel
) -> Response:
    result = await FileService.rename(model,query_db)
    return ResponseUtil.success(data=result)

@file_controller.delete(
    "/{file_id}",
    summary='删除文件',
    description='用于删除文件',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:file:delete')],
)
async def delete_file(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    file_id: int = Path(..., description="文件ID")
) -> Response:
    result = await FileService.delete(file_id, query_db)
    return ResponseUtil.success()


# @file_controller.get("/download/{filename}")
# async def download_file(filename: str):
#     """基础文件下载"""
#     file_path = UPLOAD_DIR / filename
#
#     if not file_path.exists():
#         raise HTTPException(status_code=404, detail="文件不存在")
#
#     return FileResponse(
#         path=file_path,
#         filename=filename,
#         media_type="application/octet-stream"
#     )
#
#
# @file_controller.get("/download/{filename}/inline")
# async def preview_file(filename: str):
#     """在线预览（不下载，直接在浏览器打开）"""
#     file_path = UPLOAD_DIR / filename
#
#     if not file_path.exists():
#         raise HTTPException(status_code=404, detail="文件不存在")
#
#     # 根据文件类型设置正确的 media_type
#     ext = filename.split('.')[-1].lower()
#     media_types = {
#         'jpg': 'image/jpeg',
#         'jpeg': 'image/jpeg',
#         'png': 'image/png',
#         'gif': 'image/gif',
#         'pdf': 'application/pdf',
#         'txt': 'text/plain',
#         'html': 'text/html',
#         'mp4': 'video/mp4',
#         'mp3': 'audio/mpeg',
#     }
#
#     media_type = media_types.get(ext, 'application/octet-stream')
#
#     return FileResponse(
#         path=file_path,
#         filename=filename,
#         media_type=media_type,
#         headers={"Content-Disposition": f"inline; filename={filename}"}
#     )