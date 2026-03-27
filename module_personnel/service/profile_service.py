from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from sqlalchemy.sql import ColumnElement

from module_personnel.entity.vo.admin_profile_vo import OaAdminProfilesUpdateModel
from module_admin.dao.user_dao import UserDao
from module_personnel.dao.profile_dao import AdminProfileDao
from utils.response_util import ResponseUtil
from module_personnel.dao.file_dao import FileDAO

class ProfileService:

    @staticmethod
    async def create_profile(db: AsyncSession, model: OaAdminProfilesUpdateModel) -> dict[str, Any]:
        try:
            user = model.user
            if user:
                await UserDao.edit_user_dao(db, user.model_dump(exclude_none=True))
            profiles = model.profiles
            if profiles:
                for profile in profiles:
                    profile.admin_id = model.user.user_id
                await AdminProfileDao.add_profile(db, profiles)
            return ResponseUtil.success(msg="修改成功")
        except Exception as e:
            return ResponseUtil.error(msg="修改失败")

    async def update_profile(self, db: AsyncSession, model: OaAdminProfilesUpdateModel,) -> dict[str, Any]:
        try:
            user = model.user
            if user:
                await UserDao.edit_user_dao(db, user.model_dump(exclude_none=True))
            profiles = model.profiles
            if profiles:
                await AdminProfileDao.delete_profile(db, model.user.user_id)
                for profile in profiles:
                    profile.admin_id = model.user.user_id
                await AdminProfileDao.add_profile(db, profiles)
            return ResponseUtil.success(msg="修改成功")
        except Exception as e:
            return ResponseUtil.error(msg="修改失败")

    @staticmethod
    async def get_profile(db: AsyncSession, admin_id: int, data_scope_sql: ColumnElement) -> dict[str, Any]:
        try:
            user = await UserDao.get_user_by_id(db, admin_id)
            profiles = await AdminProfileDao.get_profile_list(db, user['query_user_basic_info'],data_scope_sql)

            files = await FileDAO.get_file_by_ids(user['query_attachment_info']["userId"], db)
            result = OaAdminProfilesUpdateModel()
            result.files = files
            result.user = user['query_user_basic_info']
            result.profiles = profiles
            return ResponseUtil.success(data=result)
        except Exception as e:
            return ResponseUtil.error(msg="获取失败")
