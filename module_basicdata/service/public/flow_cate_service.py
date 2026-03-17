from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.entity.vo.public.flow_cate_vo import FlowCatePageQueryModel, OaFlowCateModel

class FlowCateService:
    @classmethod
    async def get_flow_cate_list_services(cls, query_db: AsyncSession, query_object: FlowCatePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[OaFlowCateModel] | list[dict[str, Any]]:
        query_list = await FlowCateDao.get_flow_cate_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            flow_cate_list_result = PageModel[OaFlowCateModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            flow_cate_list_result = []
            if query_list:
                flow_cate_list_result = [{**row} for row in query_list]
        return flow_cate_list_result

    @classmethod
    async def add_flow_cate_service(cls, query_db: AsyncSession, flow_cate_model: OaFlowCateModel) -> CrudResponseModel:
        try:
            flow_cate_model.create_time = int(datetime.now().timestamp() * 1000)
            await FlowCateDao.add_flow_cate(query_db, flow_cate_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e


    @classmethod
    async def update_flow_cate_service(cls, query_db: AsyncSession, flow_cate_model: OaFlowCateModel):
        try:
            flow_cate_model.update_time = int(datetime.now().timestamp() * 1000)
            await FlowCateDao.update_flow_cate(query_db,  flow_cate_model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_flow_cate_service(cls, query_db: AsyncSession, id: int):
        try:
            await FlowCateDao.delete_flow_cate(query_db, id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def get_flow_cate_info_service(cls, query_db: AsyncSession, id: int) -> OaFlowCateModel:
        try:
            flow_cate_info = await FlowCateDao.get_flow_cate_info(query_db, id)
            if not flow_cate_info:
                raise ServiceException(message="未找到该数据")
            return flow_cate_info
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def change_status_flow_cate_service(cls, query_db: AsyncSession, model: OaFlowCateModel):
        try:
            await FlowCateDao.change_status_flow_cate(query_db, model)
            return CrudResponseModel(is_success=True, message='状态修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e