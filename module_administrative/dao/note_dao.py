from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func
from common.vo import PageModel
from module_admin.entity.do.note_cate_do import SysNoteCate
from module_admin.entity.do.user_do import SysUser
from utils.page_util import PageUtil
from module_administrative.entity.vo.note_vo import OaNoteQueryPageModel, OaNoteBaseModel
from module_administrative.entity.do.note_do import OaNote
from typing import Any
from datetime import datetime

from utils.review_util import ReviewUtil


class NoteDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaNoteQueryPageModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaNote,
                        SysUser.nick_name.label('admin_name'),
                        SysNoteCate.title.label('cate_name')
                        ).join(SysUser, OaNote.admin_id == SysUser.user_id, isouter=True).join(SysNoteCate, OaNote.cate_id == SysNoteCate.id, isouter=True)

        # 构建条件列表
        conditions = []
        conditions.append(OaNote.delete_time == 0)
        conditions.append(OaNote.title.like(f'%{query_object.keyword}%')) if query_object.keyword else None

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaNote.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaNoteBaseModel):
        db_model = OaNote(**model.model_dump(exclude={"id", "create_time", "start_time", "end_time"}, exclude_none=True),
                                 create_time=model.create_time, start_time=model.start_time, end_time=model.end_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaNoteBaseModel):
        result = await db.execute(
            update(OaNote)
            .values(
                **model.model_dump(exclude={"id", "update_time" ,"start_time", "end_time"}, exclude_none=True),
                update_time=model.update_time, start_time=model.start_time, end_time=model.end_time
            )
            .where(OaNote.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaNote,
                       SysUser.nick_name.label('admin_name'),
                       SysNoteCate.title.label('cate_name')
                       ).join(SysUser, OaNote.admin_id == SysUser.user_id, isouter=True).
                 join(SysNoteCate, OaNote.cate_id == SysNoteCate.id, isouter=True)
                .where(
                    OaNote.id == id))
        result = await db.execute(query)
        info = result.mappings().first()
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaNote).values(delete_time=int(datetime.now().timestamp())).where(OaNote.id == id))
        await db.commit()
        return result.rowcount
