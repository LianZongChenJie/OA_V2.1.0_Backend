from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from typing import Any
from datetime import datetime

from common.constant import CommonConstant
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
        if not await cls.check_name_unique_services(query_db, flow_cate_model):
            raise ServiceException(message=f'新增分类{flow_cate_model.title}失败，名称已存在')
        try:
            flow_cate_model.create_time = int(datetime.now().timestamp() * 1000)
            await FlowCateDao.add_flow_cate(query_db, flow_cate_model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e


    @classmethod
    async def update_flow_cate_service(cls, query_db: AsyncSession, flow_cate_model: OaFlowCateModel):
        if not await cls.check_name_unique_services(query_db, flow_cate_model):
            raise ServiceException(message=f'修改分类{flow_cate_model.title}失败，名称已存在')
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


    @classmethod
    async def check_name_unique_services(cls, query_db: AsyncSession, page_object: OaFlowCateModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.title is None else page_object.title
        model = await FlowCateDao.get_info_by_title(query_db, OaFlowCateModel(title=page_object.title))
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        if model and model.title == title:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE