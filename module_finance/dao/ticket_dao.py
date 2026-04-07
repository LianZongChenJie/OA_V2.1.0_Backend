from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_finance.entity.vo.ticket_vo import OaTicketBaseModel, OaTicketPageQueryModel
from module_finance.entity.do.ticket_do import OaTicket,OaTicketPayment
from typing import Any
from datetime import datetime

class TicketDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaTicketPageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaTicket)

        # 构建条件列表
        conditions = []
        conditions.append(OaTicket.delete_time == 0)
        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaTicket.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaTicket.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaTicket.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaTicket.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaTicket.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaTicket.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaTicket.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaTicket.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaTicket.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaTicket.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))
        if query_object.is_code is not None:
            if query_object.is_code == 1:
                conditions.append(OaTicket.code != '')
            else:
                conditions.append(OaTicket.code == '')
        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaTicket.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaTicketBaseModel):
        db_model = OaTicket(**model.model_dump(exclude={"id", "create_time",'open_time', 'pay_time'}, exclude_none=True),
                                 create_time=model.create_time, open_time=model.open_time, pay_time=model.pay_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaTicketBaseModel):
        result = await db.execute(
            update(OaTicket)
            .values(
                **model.model_dump(exclude={"id", "update_time",'open_time', 'pay_time'}, exclude_none=True),
                update_time=model.update_time,  open_time=model.open_time, pay_time=model.pay_time,
            )
            .where(OaTicket.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaTicket)
        .where(
            OaTicket.id == id))
        info = await db.scalar(query)
        return info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaTicket).values(delete_time=int(datetime.now().timestamp())).where(OaTicket.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def review(cls, db: AsyncSession, query_model: OaTicketBaseModel):
        result = await db.execute(update(OaTicket).values(
            update_time=int(datetime.now().timestamp()),
            check_status=query_model.check_status,
            remark=query_model.remark
        ).where(OaTicket.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def open_status(cls, db: AsyncSession, query_model: OaTicketBaseModel):
        result = await db.execute(update(OaTicket).values(
            open_time=query_model.open_time,
            open_status=query_model.open_status,
            admin_id=query_model.admin_id
        ).where(OaTicket.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def payment(cls, db: AsyncSession, data: OaTicketBaseModel, userId: int):
        try:
            result = await db.execute(
                update(OaTicket)
                .values(
                    pay_time=int(datetime.now().timestamp()),
                    pay_status=1,
                    pay_admin_id=userId,
                )
                .where(OaTicket.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

# ---------------------------------- 以下为收票付款记录0_0 ----------------------------------
    @classmethod
    async def payment_add(cls, db: AsyncSession, data_list: list[OaTicketPayment]):
        insert_list = []
        for data in data_list:
            db_model = OaTicketPayment(**data.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                    create_time=data.create_time)
            insert_list.append(db_model)
        db.add_all(insert_list)
        await db.commit()

    @classmethod
    async def payment_del(cls, db: AsyncSession, ids: list[int]):
        result = await db.execute(update(OaTicketPayment).values(status=6).where(OaTicketPayment.id.in_(ids)))
        await db.commit()
        return result.rowcount

    @classmethod
    async def payment_count(cls, db: AsyncSession, ticket_id: int):
        result = await db.execute(
            select(func.count()).select_from(OaTicketPayment).where(OaTicketPayment.ticket_id == ticket_id , OaTicketPayment.status == 1)
        )
        await db.commit()
        return result.scalar()

    @classmethod
    async def ticket_get_payments(cls, db: AsyncSession, ticket_id: int):

        # 构建基础查询
        query = select(OaTicketPayment).where(OaTicketPayment.ticket_id == ticket_id, OaTicketPayment.status == 1)
        result = await db.execute(query)
        incomes = result.scalars().all()
        return incomes

    @classmethod
    async def payment_get_id(cls, db: AsyncSession, id: int):
        query = select(OaTicketPayment.ticket_id).where(OaTicketPayment.id == id)
        result = await db.execute(query)
        return result.scalar()
