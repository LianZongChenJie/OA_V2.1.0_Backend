from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import select, update,desc
from typing import Any
from common.vo import PageModel
from module_basicdata.entity.do.public.flow_module_do import FlowModule
from module_basicdata.entity.vo.public.flow_module_vo import FlowModulePageQueryModel, FlowModuleModel
from datetime import datetime, time

from utils.page_util import PageUtil


class OAFlowModuleDao:
    @classmethod
    async def get_flow_module_list(
        cls, db: AsyncSession, query_object: FlowModulePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        """
        根据查询参数获取审批模块表信息
        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql:
        :param is_page: 是否开启分页
        :return: 用模板表信息对象
        """
        query = (
            select(FlowModule)
            .where(
                FlowModule.status == '1'
                if query_object
                else True,
                FlowModule.titel.like(f'%{query_object.title}%') if query_object.title else True,
                FlowModule.create_time.between(datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
                data_scope_sql,
            ).order_by(FlowModule.create_time.desc())
        )
        flow_module_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return flow_module_list

    @classmethod
    async def add_flow_module_dao(cls, db: AsyncSession, flow_module: FlowModuleModel) -> None:
        """
        新增审批模块表信息数据库操作
        :param db: orm对象
        :param flow_module: 审批模块表信息对象
        :return:
        """
        db_flow_module = FlowModule(**flow_module.model_dump())
        db.add(db_flow_module)
        await db.commit()
        await db.refresh(db_flow_module)
        return db_flow_module

    @classmethod
    async def del_flow_module_dao(
        cls, db: AsyncSession, flow_module_id: int
    ) -> int:
        """
        删除审批模块表信息数据库操作
        :param db: orm对象
        :param flow_module_id: 审批模块表信息id
        :return:
        """
        result = await db.execute(update(FlowModule).where(FlowModule.id == flow_module_id).values(status = '-1'))
        return result.rowcount

    @classmethod
    async def change_status_flow_module_dao(
        cls, db: AsyncSession, flow_module_model: FlowModuleModel
    ) -> int:
        """
        删除审批模块表信息数据库操作
        :param status:
        :param db: orm对象
        :param flow_module_model: 审批模块表信息
        :return:
        """
        result = await db.execute(update(FlowModule).where(FlowModule.id == flow_module_model.id).values(status = flow_module_model.status))
        return result.rowcount

    @classmethod
    async def update_flow_module_dao(
        cls, db: AsyncSession, flow_module: FlowModuleModel) -> int:
        """
        更新审批模块表信息数据库操作
        :param db: orm对象
        :param flow_module: 审批模块表信息对象
        :return:
        """
        result = await db.execute(
            update(FlowModule)
            .values(**flow_module.model_dump(exclude={"id", "create_time"}, exclude_none=True), update_time = flow_module.update_time)
            .where(FlowModule.id == flow_module.id)
            )
        return result.rowcount

    @classmethod
    async def get_flow_module_by_info(cls, db: AsyncSession, flowModule: FlowModuleModel) -> FlowModule | None:
        """
        根据用户参数获取用户信息

        :param flowModule:
        :param db: orm对象
        :return: 当前用户参数的用户信息对象
        """
        query_flow_module_info = (
            (
                await db.execute(
                    select(FlowModule)
                    .where(
                        FlowModule.status == '1',
                        FlowModule.title == flowModule.title if flowModule.title else True
                    )
                    .order_by(desc(flowModule.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_flow_module_info

    @classmethod
    async def get_flow_module_by_id(cls, db: AsyncSession, flow_module_id: int) -> FlowModuleModel | None:
        """
        根据用户参数获取用户信息

        :param flow_module_id:
        :param db: orm对象
        :return: 当前用户参数的用户信息对象
        """
        query_flow_module_info = (
            (
                await db.execute(
                    select(FlowModule)
                    .where(FlowModule.id == flow_module_id,
                           FlowModule.status == '1').order_by(desc(FlowModule.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_flow_module_info