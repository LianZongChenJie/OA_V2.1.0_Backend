from operator import and_
from os import name

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.care_cate_do import SysCareCate
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_personnel.entity.vo.care_vo import OaCareBaseModel, OaCarePageQueryModel
from module_personnel.entity.do.care_do import OaCare
from typing import Any
from datetime import datetime

class CareDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaCarePageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        user = aliased(SysUser, name='user')
        query = (select(OaCare, SysUser.nick_name.label('user_name'),user.nick_name.label('admin_name'),SysCareCate.title.label('cate_name'))
                 .join(SysUser, OaCare.uid == SysUser.user_id, isouter=True)
                 .join(user, user.user_id == OaCare.admin_id, isouter=True)
                 .join(SysCareCate, OaCare.care_cate == SysCareCate.id, isouter=True)
                     .where(
                            OaCare.delete_time == 0,
                            OaCare.status == query_object.status if query_object.status else True,
                            OaCare.care_cate == query_object.care_cate if query_object.care_cate else True,
                            OaCare.uid == query_object.uid if query_object.uid else True,
                            OaCare.check_time.between(
                                int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                                int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
                            ) if query_object.begin_time and query_object.end_time else True,

                        data_scope_sql,
            ).order_by(desc(OaCare.create_time)))
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaCareBaseModel):
        db_model = OaCare(**model.model_dump(exclude={"id", "create_time","care_time"}, exclude_none=True),
                                 create_time=model.create_time, care_time = model.care_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaCareBaseModel):
        result = await db.execute(
            update(OaCare)
            .values(
                **model.model_dump(exclude={"id", "update_time", "care_time"}, exclude_none=True, ),update_time=model.update_time,care_time = model.care_time
            )
            .where(OaCare.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        user = aliased(SysUser, name='user')
        query = (select(OaCare, SysUser.nick_name.label('user_name'),user.nick_name.label('admin_name'),SysCareCate.title.label('cate_name'))
                 .join(SysUser, OaCare.uid == SysUser.user_id, isouter=True)
                 .join(user, user.user_id == OaCare.admin_id, isouter=True)
                 .join(SysCareCate, OaCare.care_cate == SysCareCate.id, isouter=True)
        .where(
            OaCare.id == id))
        link_info = await db.execute(query)
        return link_info.mappings().first()

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaCareBaseModel) -> OaCare | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaCare)
                    .where(
                        OaCare.uid == model.uid if model.uid else True
                        and OaCare.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaCare.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info

    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaCare).values(delete_time=int(datetime.now().timestamp())).where(OaCare.id == id))
        await db.commit()
        return result.rowcount

