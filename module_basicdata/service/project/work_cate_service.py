from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

from module_basicdata.dao.project.work_cate_dao import WorkCateDao
from module_basicdata.entity.vo.project.work_cate_vo import WorkCatePageQueryModel, OaWorkCateBaseModel


class WorkCateService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: WorkCatePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaWorkCateBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await WorkCateDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaWorkCateBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaWorkCateBaseModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'新增工作类别{model.title}失败，类别名称已存在')
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            await WorkCateDao.add(query_db, model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaWorkCateBaseModel):
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'修改工作类别{model.title}失败，类别名称已存在')
        try:
            model.update_time = int(datetime.now().timestamp())
            await WorkCateDao.update(query_db, model)
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_service(cls, query_db: AsyncSession, model: OaWorkCateBaseModel):
        try:
            await WorkCateDao.change_status(query_db, model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaWorkCateBaseModel:
        try:
            industry_info = await WorkCateDao.get_info_by_id(query_db, id)
            if not industry_info:
                raise ServiceException(message="未找到该数据")
            return industry_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def check_name_unique_services(cls, query_db: AsyncSession, page_object: OaWorkCateBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.title is None else page_object.title
        model = await WorkCateDao.get_info_by_title(query_db, OaWorkCateBaseModel(title=page_object.title))
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        if model and model.title == title:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE