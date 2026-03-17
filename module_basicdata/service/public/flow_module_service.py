from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime

from common.constant import CommonConstant
from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_basicdata.dao.public.flow_module_dao import OAFlowModuleDao
from module_basicdata.entity.vo.public.flow_module_vo import FlowModulePageQueryModel, FlowModuleModel


class FlowModuleService:

    @classmethod
    async def get_flow_module_list_services(cls, query_db: AsyncSession, query_object: FlowModulePageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[FlowModuleModel] | list[dict[str, Any]]:
        query_list = await OAFlowModuleDao.get_flow_module_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            flow_module_list_result =  PageModel[FlowModuleModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            flow_module_list_result = []
            if query_list:
                flow_module_list_result = [{**row} for row in query_list]
        return flow_module_list_result

    @classmethod
    async def check_flow_module_name_unique_services(cls, query_db: AsyncSession, page_object: FlowModuleModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.title is None else page_object.title
        flow_module = await OAFlowModuleDao.get_flow_module_by_info(query_db, FlowModuleModel(title=page_object.title))
        if flow_module and flow_module.title == title:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def create_flow_module_service(cls, query_db: AsyncSession, flow_module_model: FlowModuleModel) -> CrudResponseModel:
        if not await cls.check_flow_module_name_unique_services(query_db, flow_module_model):
            raise ServiceException(message=f'修改消息模板{flow_module_model.title}失败，模块名称已存在')
        try:
            flow_module_model.create_time = int(datetime.now().timestamp() * 1000)
            await OAFlowModuleDao.add_flow_module_dao(query_db, flow_module_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e


    @classmethod
    async def detail_flow_module_service(cls, query_db: AsyncSession, flow_module_id: int) -> FlowModuleModel|None:
        try:
            if flow_module_id:
                flow_module = await OAFlowModuleDao.get_flow_module_by_id(query_db, flow_module_id)
                return flow_module
        except Exception as e:
            raise e

    @classmethod
    async def update_flow_module_service(cls, query_db: AsyncSession, flow_module_model: FlowModuleModel) -> CrudResponseModel:
        update_flow_module = FlowModuleModel(**flow_module_model.model_dump(by_alias=True))
        update_flow_module.update_time = int(datetime.now().timestamp() * 1000)
        if not await cls.check_flow_module_name_unique_services(query_db, update_flow_module):
            raise ServiceException(message=f'修改审批模块{flow_module_model.title}失败，模块名称已存在')
        try:
            await OAFlowModuleDao.update_flow_module_dao(query_db, update_flow_module)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_flow_module_service(cls, query_db: AsyncSession, flow_module_id: int) -> CrudResponseModel:
        try:
            await OAFlowModuleDao.del_flow_module_dao(query_db, flow_module_id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

        pass

    @classmethod
    async def change_status_flow_module_service(cls, query_db: AsyncSession, flow_module_model: FlowModuleModel) -> CrudResponseModel:
        try:
            await OAFlowModuleDao.change_status_flow_module_dao(query_db, flow_module_model)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='状态变更成功')
        except Exception as e:
            await query_db.rollback()
            raise e