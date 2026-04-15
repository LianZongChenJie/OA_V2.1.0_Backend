from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_administrative.entity.vo.new_vo import OaNewsBaseModel, OaNewsQueryPageModel
from module_administrative.entity.do.news_do import OaNews
from typing import Any
from datetime import datetime

class NewsDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaNewsQueryPageModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaNews,
                       SysUser.nick_name.label('admin_name')).join(
                        SysUser, OaNews.admin_id == SysUser.user_id, isouter=True)

        # 构建条件列表
        conditions = []
        conditions.append(OaNews.delete_time == 0)
        conditions.append(OaNews.title.like(f'%{query_object.keyword}%')) if query_object.keyword else None
        conditions.append(OaNews.content.like(f'%{query_object.keyword}%')) if query_object.keyword else None

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaNews.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaNewsBaseModel):
        db_model = OaNews(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                 create_time=model.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaNewsBaseModel):
        result = await db.execute(
            update(OaNews)
            .values(
                **model.model_dump(exclude={"id", "update_time"}, exclude_none=True),
                update_time=model.update_time
            )
            .where(OaNews.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaNews,
                       SysUser.nick_name.label('admin_name'))
        .join(SysUser, OaNews.admin_id == SysUser.user_id, isouter=True)
        .where(OaNews.id == id))
        result = await db.execute(query)
        info = result.mappings().first()
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaNews).values(delete_time=int(datetime.now().timestamp())).where(OaNews.id == id))
        await db.commit()
        return result.rowcount
