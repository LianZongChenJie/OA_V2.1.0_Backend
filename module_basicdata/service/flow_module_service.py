from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from typing import Any

from common.vo import PageModel
from module_basicdata.entity.vo.flow_module_vo import FlowModulePageQueryModel, FlowModuleModel


class FlowModuleService:

    @classmethod
    async def get_flow_module_list_services(cls, query_db: AsyncSession, query_object: FlowModulePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[FlowModuleModel] | list[dict[str, Any]]:
        pass

    @classmethod
    async def create_flow_module_service(cls, query_db: AsyncSession, flow_module_model: FlowModuleModel) -> dict[str, Any]:
        pass

    @classmethod
    async def update_flow_module_service(cls, query_db: AsyncSession, flow_module_id: int, flow_module_model: FlowModuleModel) -> dict[str, Any]:
        pass

    @classmethod
    async def delete_flow_module_service(cls, query_db: AsyncSession, flow_module_id: int) -> dict[str, Any]:
        pass