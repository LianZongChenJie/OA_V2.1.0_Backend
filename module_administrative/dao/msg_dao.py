from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement

from module_admin.entity.do.user_do import SysUser
from module_administrative.entity.do.msg_do import OaMsg
from sqlalchemy import select, update, desc
from datetime import datetime
from common.vo import PageModel
from typing import Any
from module_administrative.entity.vo.msg_vo import OaMsgQueryPageModel, OaMsgBaseModel
from utils.page_util import PageUtil


class MsgDao:
    @classmethod
    async def add_list(cls, db: AsyncSession, msg_list: list[OaMsg]):
        for msg in msg_list:
            db.add(msg)
        result = await db.commit()
        return result

    @classmethod
    async def add(cls, db: AsyncSession, msg: OaMsgBaseModel):
        db_model = OaMsg(**msg.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                          create_time=msg.create_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def add_by_entity(cls, db: AsyncSession, entity: OaMsg):
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity.id

    @classmethod
    async def set_read(cls, db: AsyncSession, msg_ids: list[int]):
        """
        批量设置为已读消息
        :param db:
        :param msg_ids:
        :return:
        """
        query = update(OaMsg).where(OaMsg.id.in_(msg_ids)).values(read_time=int(datetime.now().timestamp()))
        result = await db.execute(query)
        await db.commit()
        return result

    @classmethod
    async def restore(cls, db: AsyncSession, msg_id:int):
        """
        批量还原消息
        :param db:
        :param msg_id:
        :return:
        """
        query = update(OaMsg).where(OaMsg.id == msg_id).values(update_time=int(datetime.now().timestamp()),delete_time=0)
        result = await db.execute(query)
        await db.commit()
        return result


    @classmethod
    async def clean_msg(cls, db: AsyncSession, msg_ids: list[int]):
        """
        批量清除消息
        :param db:
        :param msg_ids:
        :return:
        """
        query = update(OaMsg).where(OaMsg.id.in_(msg_ids)).values(clear_time=int(datetime.now().timestamp()))
        result = await db.execute(query)
        return result

    @classmethod
    async def get_msg_by_id(cls, db: AsyncSession, msg_id: int):
        from_user = aliased(SysUser, name='from_user')
        to_user = aliased(SysUser, name='to_user')
        query = (select(OaMsg,
                       from_user.nick_name.label('from_name'),
                        to_user.nick_name.label('to_name'))
                 .join(to_user, OaMsg.to_uid == to_user.user_id, isouter=True)
                 .join(from_user, OaMsg.from_uid == from_user.user_id, isouter=True)
                 .filter(OaMsg.id == msg_id))
        result = await db.execute(query)
        return result.mappings().first()


    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaMsgQueryPageModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        from_user = aliased(SysUser, name='from_user')
        to_user = aliased(SysUser, name='to_user')
        query = (select(OaMsg,
                       from_user.nick_name.label('from_name'),
                       to_user.nick_name.label('to_name')
                       )
                 .join(from_user, OaMsg.from_uid == from_user.user_id, isouter=True)
                 .join(to_user, OaMsg.to_uid == to_user.user_id,isouter=True))

        # 构建条件列表
        conditions = []
        conditions.append(OaMsg.delete_time == 0)

        conditions.append(OaMsg.title.like(f'%{query_object.keyword}%')) if query_object.keyword else None

        if query_object.begin_time and query_object.end_time:
            conditions.append(OaMsg.create_time >= query_object.begin_time)
            conditions.append(OaMsg.create_time <= query_object.end_time)

        if query_object.msg_type == 1:
            conditions.append(OaMsg.from_uid != 0)
        elif query_object.msg_type == 2:
            conditions.append(OaMsg.from_uid == 0)

        if query_object.read_status == 0:
            conditions.append(OaMsg.read_time == 0)
        elif query_object.read_status == 1:
            conditions.append(OaMsg.read_time != 0)



        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaMsg.create_time))

        # 分页查询
        page_list = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def clear(cls, db: AsyncSession, message_id: int):
        query = update(OaMsg).where(OaMsg.id == message_id).values(clear_time=int(datetime.now().timestamp()))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def delete(cls, db: AsyncSession, message_ids: list[int]):
        query = update(OaMsg).where(OaMsg.id.in_(message_ids)).values(delete_time=int(datetime.now().timestamp()))
        await db.execute(query)
        await db.commit()

    @classmethod
    async def set_star(cls, db: AsyncSession, message_ids: list[int], is_star: int):
        query = update(OaMsg).where(OaMsg.id.in_(message_ids)).values(is_star=is_star)
        await db.execute(query)
        await db.commit()

