from operator import and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.sql import ColumnElement, func,or_
from common.vo import PageModel
from utils.page_util import PageUtil
from module_personnel.entity.vo.department_change_vo import OaDepartmentChangePageQueryModel, OaDepartmentChangeBassModel
from module_personnel.entity.do.department_change_do import OaDepartmentChange
from typing import Any
from datetime import datetime

class DepartmentChangeDao:
    # @classmethod
    # async def get_page_list(cls, db: AsyncSession, query_object: OaDepartmentChangePageQueryModel,
    #                         data_scope_sql: ColumnElement,
    #                         is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
    #     if query_object.admin_id:
    #         query = (select(OaDepartmentChange)
    #                  .where(
    #                     OaDepartmentChange.check_status == query_object.check_status if query_object.check_status else True,
    #                     OaDepartmentChange.check_time.between(
    #                         int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                         int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                     ) if query_object.begin_time and query_object.end_time else True,
    #                     OaDepartmentChange.admin_id == query_object.admin_id,
    #             data_scope_sql,
    #         ).order_by(desc(OaDepartmentChange.create_time)))
    #
    #     elif query_object.check_uids:
    #         query = (select(OaDepartmentChange)
    #                  .where(
    #                     OaDepartmentChange.check_status == query_object.check_status if query_object.check_status else True,
    #                     OaDepartmentChange.check_time.between(
    #                         int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                         int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                     ) if query_object.begin_time and query_object.end_time else True,
    #                 func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0,
    #                 data_scope_sql,
    #         ).order_by(desc(OaDepartmentChange.create_time)))
    #     elif query_object.check_history_uids:
    #         query = (select(OaDepartmentChange)
    #                  .where(
    #                     OaDepartmentChange.check_status == query_object.check_status if query_object.check_status else True,
    #                     OaDepartmentChange.check_time.between(
    #                         int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                         int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                     ) if query_object.begin_time and query_object.end_time else True,
    #                 func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0,
    #                 data_scope_sql,
    #         ).order_by(desc(OaDepartmentChange.create_time)))
    #     elif query_object.check_copy_uids:
    #          query = (select(OaDepartmentChange)
    #                  .where(
    #             OaDepartmentChange.check_status == query_object.check_status if query_object.check_status else True,
    #             OaDepartmentChange.check_time.between(
    #                 int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                 int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #             ) if query_object.begin_time and query_object.end_time else True,
    #             func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0,
    #             data_scope_sql,
    #         ).order_by(desc(OaDepartmentChange.create_time)))
    #     else:
    #         query = (select(OaDepartmentChange)
    #                  .where(
    #                     and_(
    #                         OaDepartmentChange.check_status == query_object.check_status if query_object.check_status else True,
    #                         OaDepartmentChange.check_time.between(
    #                             int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                             int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp()),
    #                         ) if query_object.begin_time and query_object.end_time else True,
    #                         or_(
    #                             query_object.admin_id == OaDepartmentChange.admin_id,
    #                             func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0,
    #                             func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0,
    #                             func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0
    #                         )
    #                     ),
    #                     data_scope_sql,
    #         ).order_by(desc(OaDepartmentChange.create_time)))
    #     page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
    #         db, query, query_object.page_num, query_object.page_size, is_page
    #     )
    #     return page_list

    @classmethod
    async def get_page_list(cls, db: AsyncSession, query_object: OaDepartmentChangePageQueryModel,
                            data_scope_sql: ColumnElement,
                            is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:

        # 构建基础查询
        query = select(OaDepartmentChange)

        # 构建条件列表
        conditions = []

        # 通用条件：审核状态
        if query_object.check_status is not None:
            conditions.append(OaDepartmentChange.check_status == query_object.check_status)

        # 通用条件：审核时间范围
        if query_object.begin_time and query_object.end_time:
            start_timestamp = int(datetime.strptime(query_object.begin_time, "%Y-%m-%d %H:%M:%S").timestamp())
            end_timestamp = int(datetime.strptime(query_object.end_time, "%Y-%m-%d %H:%M:%S").timestamp())
            conditions.append(OaDepartmentChange.check_time.between(start_timestamp, end_timestamp))

        # 根据不同的查询条件添加特定条件
        if query_object.admin_id:
            conditions.append(OaDepartmentChange.admin_id == query_object.admin_id)

        elif query_object.check_uids:
            conditions.append(func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0)

        elif query_object.check_history_uids:
            conditions.append(
                func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0)

        elif query_object.check_copy_uids:
            conditions.append(func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0)

        else:
            # 没有特定条件时，使用 OR 组合
            or_conditions = []
            if query_object.admin_id:
                or_conditions.append(OaDepartmentChange.admin_id == query_object.admin_id)
            if query_object.check_uids:
                or_conditions.append(func.find_in_set(query_object.check_uids, OaDepartmentChange.check_uids) > 0)
            if query_object.check_copy_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_copy_uids, OaDepartmentChange.check_copy_uids) > 0)
            if query_object.check_history_uids:
                or_conditions.append(
                    func.find_in_set(query_object.check_history_uids, OaDepartmentChange.check_history_uids) > 0)

            if or_conditions:
                conditions.append(or_(*or_conditions))

        # 添加数据权限条件
        if data_scope_sql is not None:
            conditions.append(data_scope_sql)

        # 应用所有条件
        if conditions:
            query = query.where(*conditions)

        # 排序
        query = query.order_by(desc(OaDepartmentChange.create_time))

        # 分页查询
        page_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return page_list

    @classmethod
    async def add(cls, db: AsyncSession, model: OaDepartmentChangeBassModel):
        db_model = OaDepartmentChange(**model.model_dump(exclude={"id", "create_time",'move_time','connect_time'}, exclude_none=True),
                                 create_time=model.create_time, move_time = model.move_time, connect_time = model.connect_time)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model
        pass

    @classmethod
    async def update(cls, db: AsyncSession, model: OaDepartmentChangeBassModel):
        result = await db.execute(
            update(OaDepartmentChange)
            .values(
                **model.model_dump(exclude={"id", "update_time",'move_time', 'connect_time'}, exclude_none=True), update_time=model.update_time, move_time = model.move_time, connect_time = model.connect_time
            )
            .where(OaDepartmentChange.id == model.id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_info_by_id(cls, db: AsyncSession, id: int):
        query = (select(OaDepartmentChange)
        .where(
            OaDepartmentChange.id == id))
        link_info = await db.scalar(query)
        return link_info

    @classmethod
    async def get_info_by_uid(cls, db: AsyncSession, model: OaDepartmentChangeBassModel) -> OaDepartmentChange | None:
        """
        根据标题获取信息

        :param model:
        :param db: orm对象
        :return:
        """
        query_info = (
            (
                await db.execute(
                    select(OaDepartmentChange)
                    .where(
                        OaDepartmentChange.uid == model.uid if model.uid else True
                        and OaDepartmentChange.check_status != 2 if model.check_status else True
                    )
                    .order_by(desc(OaDepartmentChange.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info
    @classmethod
    async def del_by_id(cls, db: AsyncSession, id: int):
        result = await db.execute(update(OaDepartmentChange).values(delete_time=int(datetime.now().timestamp())).where(OaDepartmentChange.id == id))
        await db.commit()
        return result.rowcount

    @classmethod
    async def review(cls, db: AsyncSession, data: OaDepartmentChangeBassModel):
        try:
            await db.execute(
                update(OaDepartmentChange)
                .values(
                    check_status=data.check_status,
                    check_time=data.check_time
                )
                .where(OaDepartmentChange.id == data.id)
            )
            await db.commit()
            return await cls.get_info_by_id(db, data.id)
        except Exception as e:
            await db.rollback()
            raise e