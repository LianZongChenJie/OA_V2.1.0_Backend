from sqlalchemy import union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql import select, func,desc, update, text

from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.user_do import SysUser
from module_administrative.entity.do.message_do import OaMessage
from module_administrative.entity.do.msg_do import OaMsg
from module_administrative.entity.vo.message_vo import OaMessagePageQueryModel, OaMessageBaseModel
from typing import Any
from datetime import datetime
from common.vo import PageModel
from utils.page_util import PageUtil


class MessageDao:
    """
    发消息dao
    """
    @classmethod
    async def get_list(cls, db: AsyncSession, query_object: OaMessagePageQueryModel,
                       data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        tu = aliased(SysUser, name="tu")
        cu = aliased(SysUser, name="cu")
        query = (select(OaMessage,
                        tu.nick_name.label('to_name'),
                        cu.nick_name.label('copy_name'),
                        SysDept.dept_name.label('dept_name'),
                        SysPost.post_name.label('post_name')
                        )
                 .join(tu, OaMessage.from_uid == tu.user_id, isouter=True)
                 .join(cu, func.find_in_set(cu.user_id, OaMessage.copy_uids), isouter=True)
                 .join(SysDept, func.find_in_set(SysDept.dept_id, OaMessage.dids), isouter=True)
                 .join(SysPost, func.find_in_set(SysPost.post_id, OaMessage.pids), isouter=True)
                 )
        conditions = []
        conditions.append(OaMessage.delete_time == 0)
        if not query_object.is_draft is None:
            conditions.append(OaMessage.is_draft == query_object.is_draft)
        else:
            conditions.append(OaMessage.is_draft == 1)

        # 通用条件：消息时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d").timestamp()) + (24 * 60 * 60 - 1)
            conditions.append(OaMessage.create_time.between(start_timestamp, end_timestamp))
        if query_object.keyword:
            conditions.append(OaMessage.title.like(f'%{query_object.keyword}%'))
        if query_object.from_uid:
            conditions.append(OaMessage.from_uid == query_object.from_uid)
        conditions.append(data_scope_sql)
        # 应用所有条件
        if conditions:
            query = query.where(*conditions).group_by(OaMessage.id)


        # 排序
        query = query.order_by(desc(OaMessage.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def get_detail(cls, db: AsyncSession, message_id: int):
        tu = aliased(SysUser, name="tu")
        cu = aliased(SysUser, name="cu")
        query = (select(OaMessage,
                        tu.nick_name.label('to_name'),
                        cu.nick_name.label('copy_name'),
                        SysDept.dept_name.label('dept_name'),
                        SysPost.post_name.label('post_name')
                        )
                 .join(tu, OaMessage.from_uid == tu.user_id, isouter=True)
                 .join(cu, func.find_in_set(cu.user_id, OaMessage.copy_uids), isouter=True)
                 .join(SysDept, func.find_in_set(SysDept.dept_id, OaMessage.dids), isouter=True)
                 .join(SysPost, func.find_in_set(SysPost.post_id, OaMessage.pids), isouter=True)
                 ).where(OaMessage.id == message_id)
        result = await db.execute(query)
        return result.mappings().first()

    @classmethod
    async def add(cls, db: AsyncSession, model: OaMessageBaseModel):
        db_model = OaMessage(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True))
        db_model.create_time = int(datetime.now().timestamp())
        db_model.template = ''
        if not db_model.uids:
            db_model.uids = ''
        if not db_model.dids:
            db_model.dids = ''
        if not db_model.pids:
            db_model.pids = ''
        if not db_model.copy_uids:
            db_model.copy_uids = ''
        if not db_model.send_time:
            db_model.send_time = 0
        if not db_model.delete_time:
            db_model.delete_time = 0
        if not db_model.update_time:
            db_model.update_time = 0
        if not db_model.clear_time:
            db_model.clear_time = 0
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, update_model: OaMessageBaseModel):
        query = (update(OaMessage).values(**update_model.model_dump(exclude={"id", "update_time"}, exclude_none=True),
                update_time=update_model.update_time)
                 .where(OaMessage.id == update_model.id))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def update_by_entity(cls, db: AsyncSession, update_model: OaMessage):
        await db.merge(update_model)
        await db.commit()

    @classmethod
    async def delete(cls, db: AsyncSession, message_ids: list[int]):
        query = (update(OaMessage).values(delete_time = int(datetime.now().timestamp()), update_time =  int(datetime.now().timestamp()))
                 .where(OaMessage.id.in_(message_ids)))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def restore(cls, db: AsyncSession, message_id: int):
        query = (update(OaMessage).values({'delete_time': 0, 'update_time': int(datetime.now().timestamp())})
                 .where(OaMessage.id == message_id))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def clear(cls, db: AsyncSession, message_id: int):
        query = (update(OaMessage).values({'clear_time': int(datetime.now().timestamp()), 'update_time': int(datetime.now().timestamp())})
                 .where(OaMessage.id == message_id))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def get_delete_msg(cls, db: AsyncSession, user_id: int, query_object: OaMessagePageQueryModel,
                       data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        from_user = aliased(SysUser, name='from_user')
        to_user = aliased(SysUser, name='to_user')

        # 收件箱（不会有重复问题）
        inbox_stmt = (select(
            text("'收件箱' as source"),
            OaMsg.id,
            OaMsg.title,
            OaMsg.from_uid,
            OaMsg.to_uid,
            OaMsg.delete_time,
            OaMsg.create_time,
            from_user.nick_name.label('from_name'),
            text("'-' as copy_name")
        )
        .join(from_user, from_user.user_id == OaMsg.from_uid, isouter=True)
        .where(
            OaMsg.delete_time != 0,
            OaMsg.to_uid == user_id
        ))

        # 发件箱和草稿箱使用子查询处理抄送人
        # 先构建抄送人聚合子查询
        copy_agg = (
            select(
                OaMessage.id.label('msg_id'),
                func.group_concat(func.distinct(SysUser.nick_name)).label('copy_names')
            )
            .join(SysUser, func.find_in_set(SysUser.user_id, OaMessage.copy_uids))
            .group_by(OaMessage.id)
            .subquery()
        )

        # 发件箱
        send_stmt = (select(
            text("'发件箱' as source"),
            OaMessage.id,
            OaMessage.title,
            OaMessage.from_uid,
            text("'-' as to_uid"),
            OaMessage.delete_time,
            OaMessage.create_time,
            from_user.nick_name.label('from_name'),
            func.coalesce(copy_agg.c.copy_names, '-').label('copy_name')
        )
        .join(from_user, from_user.user_id == OaMessage.from_uid, isouter=True)
        .outerjoin(copy_agg, copy_agg.c.msg_id == OaMessage.id)
        .where(
            OaMessage.delete_time != 0,
            OaMessage.from_uid == user_id,
            OaMessage.send_time != 0,
            data_scope_sql
        ))

        # 草稿箱（结构同发件箱）
        draft_stmt = (select(
            text("'草稿箱' as source"),
            OaMessage.id,
            OaMessage.title,
            OaMessage.from_uid,
            text("'-' as to_uid"),
            OaMessage.delete_time,
            OaMessage.create_time,
            from_user.nick_name.label('from_name'),
            func.coalesce(copy_agg.c.copy_names, '-').label('copy_name')
        )
        .join(from_user, from_user.user_id == OaMessage.from_uid, isouter=True)
        .outerjoin(copy_agg, copy_agg.c.msg_id == OaMessage.id)
        .where(
            OaMessage.delete_time != 0,
            OaMessage.from_uid == user_id,
            OaMessage.send_time == 0,
            data_scope_sql
        ))

        # 合并
        query = union_all(inbox_stmt, draft_stmt, send_stmt)

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list