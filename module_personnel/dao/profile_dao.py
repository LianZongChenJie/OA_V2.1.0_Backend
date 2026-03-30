from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update, desc, asc, delete, insert


from typing import Any
from common.vo import PageModel
from module_admin.entity.vo.user_vo import UserModel
from module_personnel.entity.do.admin_profile_do import OaAdminProfiles
from module_personnel.entity.vo.admin_profile_vo import OaAdminProfilesUpdateModel, OaAdminProfilesBaseModel
from utils.page_util import PageUtil

class AdminProfileDao:

    # 获取员工档案
    @classmethod
    async def get_profile_list(cls, db: AsyncSession, query_object: UserModel) -> PageModel | list[
        list[dict[str, Any]]]:
        query = (select(OaAdminProfiles)
                 .where(
            OaAdminProfiles.admin_id == query_object.user_id,
        ).order_by(asc(OaAdminProfiles.types)))
        profile_list = (await  db.execute(query)).scalars().all()
        return profile_list

    @classmethod
    async def delete_profile(cls, db: AsyncSession, user_id: int) -> dict[str, Any] | None:
        query = (delete(OaAdminProfiles).where(
            OaAdminProfiles.admin_id == user_id,
        ))
        await  db.execute(query)

    # 添加员工档案
    @classmethod
    async def add_profile(cls, db: AsyncSession, profiles : list[OaAdminProfilesBaseModel]) -> dict[str, Any] | None:
        add_list = []
        for profile in profiles:
            if profile:
                data = profile.dict(exclude_none=True, exclude={'id'})

                # 使用字典创建实体
                entity = OaAdminProfiles(**data)
                add_list.append(entity)
        # 批量添加
        db.add_all(add_list)

        # 提交事务
        result = await db.commit()
        return result
