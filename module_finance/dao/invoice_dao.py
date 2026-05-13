from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.orm import aliased
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from module_basicdata.entity.do.public.enterprise_do import OaEnterprise
from utils.page_util import PageUtil
from module_finance.entity.vo.invoice_vo import OaInvoiceBaseModel, OaInvoicePageQueryModel
from module_finance.entity.do.invoice_do import OaInvoice, OaInvoiceIncome
from typing import Any
from datetime import datetime

class InvoiceDao:
    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaInvoicePageQueryModel,
                            data_scope_sql: ColumnElement, user_id: int,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 创建子查询获取每个发票的最新回款时间
        latest_income_subq = (
            select(
                OaInvoiceIncome.invoice_id,
                func.max(OaInvoiceIncome.enter_time).label('latest_enter_time'),
                # 可选：同时获取最新回款的金额
                func.max(OaInvoiceIncome.amount).label('latest_amount')
            )
            .where(OaInvoiceIncome.status == 1)  # 只统计有效记录
            .group_by(OaInvoiceIncome.invoice_id)
            .subquery('latest_income')
        )

        # 构建基础查询
        admin = aliased(SysUser, name='admin')
        open = aliased(SysUser, name='open')
        dept = aliased(SysDept, name='dept')
        enter = aliased(OaEnterprise, name='enter')
        check = aliased(SysUser, name='check')
        query = (select(OaInvoice,
                        admin.nick_name.label('admin_name'),
                        open.nick_name.label('open_name'),
                        dept.dept_name.label('dept_name'),
                        enter.title.label('enter_name'),
                        func.group_concat(check.nick_name, ',').label('check_name'),
                        # 添加最新回款时间字段
                        func.coalesce(latest_income_subq.c.latest_enter_time, 0).label('latest_enter_time'),
                        # 可选：添加最新回款金额
                        func.coalesce(latest_income_subq.c.latest_amount, 0).label('latest_amount')
                        )

        .join(admin, OaInvoice.admin_id == admin.user_id, isouter=True)
        .join(open, OaInvoice.open_admin_id == open.user_id, isouter=True)
         .join(dept, OaInvoice.did == dept.dept_id, isouter=True)
         .join(enter, OaInvoice.invoice_subject == enter.id, isouter=True)
         .join(check, func.find_in_set(check.user_id, OaInvoice.check_uids), isouter=True)
         # 关联最新回款子查询
         .outerjoin(latest_income_subq, OaInvoice.id == latest_income_subq.c.invoice_id)
                 )

        # 构建条件列表
        conditions = []
        conditions.append(OaInvoice.delete_time == 0)
        if query_object.tab == 1:
            conditions.append(OaInvoice.admin_id == user_id)
        if query_object.tab == 2:
            conditions.append(func.find_in_set(user_id, OaInvoice.check_uids) > 0)
        if query_object.tab == 3:
            conditions.append(func.find_in_set(user_id, OaInvoice.check_history_uids) > 0)
        if query_object.tab == 4:
            conditions.append(func.find_in_set(user_id, OaInvoice.check_copy_uids) > 0)
        if query_object.tab == 5:
            conditions.append(OaInvoice.enter_status == 2)
        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaInvoice.check_status == query_object.check_status)

        if query_object.open_status is not None:
            conditions.append(OaInvoice.open_status == query_object.open_status)


        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaInvoice.check_time.between(start_timestamp, end_timestamp))
        # 打款状态
        if query_object.enter_status is not None:
            conditions.append(OaInvoice.enter_status == query_object.enter_status)
        # 开票状态
        if query_object.open_status is not None:
            conditions.append(OaInvoice.open_status == query_object.open_status)

        # 根据不同的查询条件添加特定条件
        if query_object.invoice_type ==0:
            conditions.append(OaInvoice.invoice_type == query_object.invoice_type)
        else:
            conditions.append(OaInvoice.invoice_type != 0)

        if query_object.admin_id:
            conditions.append(OaInvoice.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaInvoice.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaInvoice.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaInvoice.check_copy_uids) > 0)

        elif query_object.invoice_type:
            conditions.append(OaInvoice.invoice_type == query_object.invoice_type)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaInvoice.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaInvoice.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaInvoice.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaInvoice.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))
        if query_object.is_code is not None:
            if query_object.is_code == 1:
                conditions.append(OaInvoice.code != '')
            else:
                conditions.append(OaInvoice.code == '')
        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions).group_by(OaInvoice.id)

        # 排序
        query = query.order_by(desc(OaInvoice.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaInvoiceBaseModel):
        db_model = OaInvoice(**model.model_dump(exclude={"id", "create_time",'open_time', 'enter_time'}, exclude_none=True),
                                 create_time=model.create_time, open_time=model.open_time, enter_time=model.enter_time)
        if db_model.project_id is None or db_model.project_id == '':
            db_model.project_id = 0
        if db_model.contract_id is None or db_model.contract_id == '':
            db_model.contract_id = 0
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: OaInvoiceBaseModel):
        result = await db.execute(
            update(OaInvoice)
            .values(
                **model.model_dump(exclude={"id", "update_time",'open_time', 'enter_time', 'project_id', 'contract_id'}, exclude_none=True),
                update_time=model.update_time,  open_time=model.open_time, enter_time=model.enter_time, project_id = model.project_id, contract_id = model.contract_id
            )
            .where(OaInvoice.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def update_by_entity(cls,db: AsyncSession, model: OaInvoice):
        result= await db.merge(model)
        await db.commit()
        return result

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        admin = aliased(SysUser, name='admin')
        open = aliased(SysUser, name='open')
        dept = aliased(SysDept, name='dept')
        enter = aliased(OaEnterprise, name='enter')
        query = (select(OaInvoice,
                        admin.nick_name.label('admin_name'),
                        open.nick_name.label('open_name'),
                        dept.dept_name.label('dept_name'),
                        enter.title.label('enter_name')
                        )
            .join(admin, OaInvoice.admin_id == admin.user_id, isouter=True)
            .join(open, OaInvoice.open_admin_id == open.user_id, isouter=True)
            .join(dept, OaInvoice.did == dept.dept_id, isouter=True)
            .join(enter, OaInvoice.invoice_subject == enter.id, isouter=True)
            .where(OaInvoice.id == id))
        info = await db.execute(query)
        return info.mappings().first()
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaInvoice).values(delete_time=int(datetime.now().timestamp())).where(OaInvoice.id == id))
        await db.commit()
        return result.rowcount


    @classmethod
    async def open_status(cls, db: AsyncSession, query_model: OaInvoiceBaseModel):
        result = await db.execute(update(OaInvoice).values(
            code = query_model.code,
            open_time=query_model.open_time,
            open_status=query_model.open_status,
            delivery=query_model.delivery,
            open_admin_id=query_model.open_admin_id
        ).where(OaInvoice.id == query_model.id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def payment(cls, db: AsyncSession, data: OaInvoiceBaseModel, userId: int):
        try:
            result = await db.execute(
                update(OaInvoice)
                .values(
                    pay_time=int(datetime.now().timestamp()),
                    pay_status=1,
                    pay_admin_id=userId,
                )
                .where(OaInvoice.id == data.id)
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            raise e

# ---------------------------------- 以下为发票到账记录0_0 ----------------------------------
    @classmethod
    async def income_add(cls, db: AsyncSession, data_list: list[OaInvoiceIncome]):
        insert_list = []
        for data in data_list:
            db_model = OaInvoiceIncome(**data.model_dump(exclude={"id", "create_time"}, exclude_none=True),
                                    create_time=data.create_time)
            insert_list.append(db_model)
        db.add_all(insert_list)
        await db.commit()

    @classmethod
    async def income_del(cls, db: AsyncSession, ids: list[int]):
        result = await db.execute(update(OaInvoiceIncome).values(status=6).where(OaInvoiceIncome.id.in_(ids)))
        await db.commit()
        return result.rowcount

    @classmethod
    async def income_income_count(cls, db: AsyncSession, invoice_id: int):
        result = await db.execute(
            select(func.count()).select_from(OaInvoiceIncome).where(OaInvoiceIncome.invoice_id == invoice_id , OaInvoiceIncome.status == 1)
        )
        await db.commit()
        return result.scalar()

    @classmethod
    async def income_get_incomes(cls, db: AsyncSession, invoice_id: int):

        # 构建基础查询
        query = select(OaInvoiceIncome).where(OaInvoiceIncome.invoice_id == invoice_id, OaInvoiceIncome.status == 1)
        result = await db.execute(query)
        incomes = result.scalars().all()
        return incomes

    @classmethod
    async def income_get_id(cls, db: AsyncSession, id: int):
        """只查询需要的字段"""
        query = select(
            OaInvoiceIncome.id,
            OaInvoiceIncome.invoice_id,
            OaInvoiceIncome.amount,
            OaInvoiceIncome.enter_time,
            OaInvoiceIncome.status
        ).where(OaInvoiceIncome.id == id)

        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        # 返回一个简单对象或字典
        return {
            'id': row.id,
            'invoice_id': row.invoice_id,
            'amount': row.amount,
            'enter_time': row.enter_time,
            'status': row.status
        }
    @classmethod
    async def get_invoice_count(cls, db: AsyncSession, user_id: int):
        query = select(func.count()).select_from(OaInvoice).where(OaInvoice.admin_id == user_id, OaInvoice.open_status == 1, OaInvoice.delete_time == 0)
        count = await db.execute(query)
        return count.scalar()

    @classmethod
    async def get_wait_check_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审开票数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审开票数量
        """
        query = select(func.count()).select_from(OaInvoice).where(
            OaInvoice.delete_time == 0,
            OaInvoice.check_status == 1,
            func.find_in_set(str(user_id), OaInvoice.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count

    @classmethod
    async def get_invoices_incomes_detail(cls, db: AsyncSession, query_model: OaInvoicePageQueryModel, data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaInvoiceIncome,
                       OaInvoice.invoice_title.label('invoice_title'),
                       OaInvoice.open_status.label('open_status'),
                       OaInvoice.create_time.label('apply_time'),
                        SysUser.nick_name.label('user_name'),
                        SysDept.dept_name.label('dept_name'))
        .join(OaInvoice,OaInvoice.id == OaInvoiceIncome.invoice_id, isouter=True)
        .join(SysUser,SysUser.user_id == OaInvoice.admin_id, isouter=True)
        .join(SysDept,SysDept.dept_id == OaInvoice.did, isouter=True)
        .where(
            OaInvoiceIncome.invoice_id == query_model.id if query_model.id else True,
            OaInvoice.invoice_title.like(f'%{query_model.invoice_title}%') if query_model.invoice_title else True,
            OaInvoiceIncome.status == 1,
            data_scope_sql,
        ))
        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate_dict(
            db, query, query_model.page_num, query_model.page_size, is_page
        )
        return page_list

