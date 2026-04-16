from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.vo import PageModel
from module_admin.entity.do.user_do import SysUser
from module_basicdata.entity.do.public.flow_cate_do import OaFlowCate
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_basicdata.entity.do.public.flow_module_do import FlowModule
from module_basicdata.entity.vo.public.flow_vo import OaFlowPageQueryModel, OaFlowBaseModel
from typing import Any
from sqlalchemy import select, update, desc, asc

from utils.page_util import PageUtil


class OaFlowDao:
    @classmethod
    async def get_flow_list(cls, db: AsyncSession, query_object: OaFlowPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel | list[list[dict[str, Any]]]:
        query = (select(OaFlow,OaFlowCate, FlowModule,SysUser)
                 .join(OaFlowCate, OaFlow.cate_id == OaFlowCate.id, isouter=True)
                 .join(FlowModule, OaFlowCate.module_id == FlowModule.id, isouter=True)
                 .join(SysUser, OaFlow.copy_uids == SysUser.user_id, isouter=True)
                 .where(
            OaFlow.status != "-1"
            if query_object
            else True,
            data_scope_sql,
        ).order_by(asc(OaFlow.id)))
        flow_cate_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )
        return flow_cate_list

    @classmethod
    async def add_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        db_flow = OaFlow(**model.model_dump(exclude={"id", "create_time"}, exclude_none=True), create_time = model.create_time)
        db.add(db_flow)
        await db.commit()
        await db.refresh(db_flow)
        return db_flow

    @classmethod
    async def update_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        result = await db.execute(
            update(OaFlow).where(model.id == OaFlow.id).values(**model.model_dump(exclude={"id","update_time"}, exclude_none=True), update_time = model.update_time)
        )
        await db.commit()
        return result

    @classmethod
    async def change_status_flow(cls, db: AsyncSession, model: OaFlowBaseModel):
        result = await db.execute(update(OaFlow).where(model.id == OaFlow.id).values(status=model.status))
        await db.commit()
        return result

    @classmethod
    async def get_flow_detail(cls, db: AsyncSession, id: int):
        result = await db.execute(select(OaFlow).where(id == OaFlow.id))
        return result.scalars().first()

    @classmethod
    async def get_info_by_title(cls, db: AsyncSession, model: OaFlowBaseModel) -> OaFlow | None:
        """
        根据用户参数获取用户信息

        :param model:
        :param db: orm对象
        :return: 对象
        """
        query_info = (
            (
                await db.execute(
                    select(OaFlow)
                    .where(
                        OaFlow.status == '1',
                        OaFlow.title == model.title if model.title else True
                    )
                    .order_by(desc(OaFlow.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_info

    @classmethod
    async def get_flow_info_by_cate_id(cls, db: AsyncSession, cate_id: int) -> OaFlow | None:
        """
        通过cate_id获取flow信息
        :param db:
        :param cate_id:
        :return:
        """
        query = select(OaFlow).where(OaFlow.cate_id == cate_id, OaFlow.status == '1', OaFlow.delete_time == 0)
        result = await db.execute(query)
        return result.scalars().first()