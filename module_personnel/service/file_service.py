import hashlib
import os
from datetime import datetime

from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.exception import ServiceException
from module_admin.dao.user_dao import UserDao
from module_admin.entity.vo.tender_vo import CrudResponseModel
from module_personnel.dao.file_dao import FileDAO
from module_personnel.entity.do.file_do import OaFile
from module_personnel.entity.vo.file_vo import OaFileBaseModel
from module_personnel.util.file_config import UPLOAD_DIR
from module_personnel.util.file_utils import generate_file_path, generate_file_name, save_upload_file, delete_file
from module_personnel.util.mimetype import MIMETYPES
from utils.camel_converter import ModelConverter
from utils.timeformat import format_timestamp

module = 'admin'
class FileService:
    @classmethod
    async def add_file(cls, files: list[UploadFile], db: AsyncSession, user_id: int) -> list[OaFileBaseModel]:
        uploaded_files = await cls.upload_file(files, user_id)
        profiles = await FileDAO.add_profiles(db, uploaded_files)
        result_list = []
        for profile in profiles:
            pro = {
                'id': profile.id,
                'name': profile.name,
                'file_name': profile.filename,
                'file_path': profile.filepath,
                'file_size': profile.filesize,
                'file_mime': profile.mimetype,
                'file_ext': profile.fileext,
                'create_time': format_timestamp(profile.create_time),
                'create_name': ','.join([name for name in (await UserDao.get_nick_name_by_user_id(db, [int(profile.user_id)]))]),

            }
            result_list.append(ModelConverter.convert_to_camel_case(pro))
        return result_list


    @classmethod
    async def upload_file(cls, files: list[UploadFile], user_id: int) -> list[OaFile]:
        action = 'upload'
        use = 'thumb'
        uploaded_files = []
        for file in files:
            try:
                # 保存文件
                old_file_name = file.filename
                file_path = generate_file_path(UPLOAD_DIR)
                safe_filename = generate_file_name(file.filename)
                file_path = os.path.join(file_path, safe_filename)

                file_len = await save_upload_file(file, file_path)

                # 计算文件信息
                file.file.seek(0)
                content = await file.read()
                profile = OaFile()
                profile.module = module
                profile.sha1 = hashlib.sha1(content).hexdigest()
                profile.md5 = hashlib.md5(content).hexdigest()
                profile.name = old_file_name
                profile.filename = safe_filename
                profile.filepath = file_path
                profile.thumbpath = None
                profile.filesize = file_len
                profile.fileext = file.filename.split('.')[-1]
                # 根据文件扩展名从MIMETYPES字典中获取对应的MIME类型，若未找到则默认为空字符串
                profile.mimetype = MIMETYPES.get(profile.fileext, '')
                profile.user_id = user_id
                profile.admin_id = user_id
                profile.create_time = int(datetime.now().timestamp())
                profile.audit_time = int(datetime.now().timestamp())
                profile.action = action
                profile.use = use
                profile.download = 0
                uploaded_files.append(profile)
            except Exception as e:
                print(e)
        return uploaded_files

    @classmethod
    async def rename(cls, file: OaFileBaseModel, db: AsyncSession) -> CrudResponseModel:
        if file is None:
            raise ServiceException(message='文件不存在')
        file = await FileDAO.get_file_by_id(file.id, db)
        if file is None:
            raise ServiceException(message='文件不存在')
        await FileDAO.rename_file(db, file)
        return CrudResponseModel(is_success=True, msg='文件重命名成功')

    @classmethod
    async def delete(cls, file_id: int, db: AsyncSession):
        ext_file = await FileDAO.get_file_by_id(file_id, db)
        if ext_file is None:
            raise ServiceException(message='文件不存在')
        try:
            await delete_file(ext_file.filepath)
            await FileDAO.delete_file(file_id, db)
            return CrudResponseModel(is_success=True, message='文件删除成功')
        except Exception as e:
            raise ServiceException(message='文件删除失败')

    @classmethod
    async def download_file(cls, db: AsyncSession, file_id: int)-> FileResponse:
        file = await FileDAO.get_file_by_id(file_id, db)
        if file is None:
            raise ServiceException(message='文件不存在')
        return FileResponse(
            path=file.filepath,
            filename=file.name,
            media_type=file.mimetype,
            content_disposition_type="attachment"
        )
