from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_dao import OaFlowDao
from module_basicdata.entity.vo.public.flow_vo import OaFlowBaseModel
from datetime import datetime

class FlowService:
    @staticmethod
    async def get_flow_detail(query_db: AsyncSession, id: int) -> OaFlowBaseModel:
        try:
            flow_cate_info = await OaFlowDao.get_flow_detail(query_db, id)
            if not flow_cate_info:
                raise ServiceException(message="未找到该数据")
            return flow_cate_info
        except Exception as e:
            await query_db.rollback()
            raise e

    @staticmethod
    async def update_flow(query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        try:
            result = await OaFlowDao.update_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='更新成功')
            return CrudResponseModel(is_success=False, message='更新失败')
        except Exception as e:
            await query_db.rollback()
            raise e

    @staticmethod
    async def add_flow(query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        try:
            model.create_time = int(datetime.now().timestamp() * 1000)
            result = await OaFlowDao.add_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='新增成功')
            return CrudResponseModel(is_success=False, message='新增失败')
        except Exception as e:
            await query_db.rollback()
            raise e

    @staticmethod
    async def change_status_flow(query_db: AsyncSession, model: OaFlowBaseModel) -> CrudResponseModel:
        try:
            result = await OaFlowDao.change_status_flow(query_db, model)
            if result:
                return CrudResponseModel(is_success=True, message='更新成功')
            return CrudResponseModel(is_success=False, message='更新失败', data=False)
        except Exception as e:
            await query_db.rollback()
            raise e

    @staticmethod
    async def get_flow_list(query_db: AsyncSession, model: OaFlowBaseModel, data_scope_sql: ColumnElement, is_page: bool) -> PageModel[OaFlowBaseModel]:
        try:
            return await OaFlowDao.get_flow_list(query_db, model, data_scope_sql, is_page)
        except Exception as e:
            await query_db.rollback()
            raise e