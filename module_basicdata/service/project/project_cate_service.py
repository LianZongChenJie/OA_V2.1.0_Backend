from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.constant import CommonConstant
from exceptions.exception import ServiceException
from common.vo import PageModel, CrudResponseModel
from typing import Any
from datetime import datetime

from module_basicdata.dao.project.project_cate_dao import ProjectCateDao
from module_basicdata.entity.vo.project.project_cate_vo import OaProjectCateBaseModel, ProjectCatePageQueryModel


class ProjectCateService:
    @classmethod
    async def get_page_list_service(cls, query_db: AsyncSession, query_object: ProjectCatePageQueryModel,
                                    data_scope_sql: ColumnElement, is_page: bool = False) -> PageModel[
                                                                                                 OaProjectCateBaseModel] | \
                                                                                             list[dict[str, Any]]:
        query_list = await ProjectCateDao.get_page_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            result_list = PageModel[OaProjectCateBaseModel](**{
                **query_list.model_dump(by_alias=True)
            })
        else:
            result_list = []
            if query_list:
                result_list = [{**row} for row in query_list]
        return result_list

    @classmethod
    async def add_service(cls, query_db: AsyncSession, model: OaProjectCateBaseModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'新增项目阶段{model.title}失败，阶段名称已存在')
        try:
            model.create_time = int(datetime.now().timestamp())
            model.status = 1
            await ProjectCateDao.add(query_db, model)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def update_service(cls, query_db: AsyncSession, model: OaProjectCateBaseModel):
        if not await cls.check_name_unique_services(query_db, model):
            raise ServiceException(message=f'修改项目阶段{model.title}失败，阶段名称已存在')
        try:
            model.update_time = int(datetime.now().timestamp())
            await ProjectCateDao.update(query_db, model)
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def change_status_service(cls, query_db: AsyncSession, model: OaProjectCateBaseModel):
        try:
            await ProjectCateDao.change_status(query_db, model)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_info_service(cls, query_db: \
            AsyncSession, id: int) -> OaProjectCateBaseModel:
        try:
            industry_info = await ProjectCateDao.get_info_by_id(query_db, id)
            if not industry_info:
                raise ServiceException(message="未找到该数据")
            return industry_info
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def check_name_unique_services(cls, query_db: AsyncSession, page_object: OaProjectCateBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        title = -1 if page_object.title is None else page_object.title
        model = await ProjectCateDao.get_info_by_title(query_db, OaProjectCateBaseModel(title=page_object.title))
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        if model and model.title == title:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE