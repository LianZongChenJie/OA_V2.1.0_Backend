from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement
from sqlalchemy import Integer
from typing import Any
from datetime import datetime
from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_basicdata.dao.template_dao import OaTemplateDao
from module_basicdata.entity.vo.template_vo import TemplateRowModel, TemplatePageQueryModel, TemplateBaseModel


class TemplateService:
    """
    用户管理模块服务层
    """

    @classmethod
    async def get_user_list_services(
        cls,
        query_db: AsyncSession,
        query_object: TemplatePageQueryModel,
        data_scope_sql: ColumnElement,
        is_page: bool = False,
    ) -> PageModel[TemplateRowModel] | list[dict[str, Any]]:
        """
        获取用户列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        query_result = await OaTemplateDao.get_template_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            template_list_result = PageModel[TemplateRowModel](
                **{
                    **query_result.model_dump(by_alias=True)
                }
            )
        else:
            user_list_result = []
            if query_result:
                user_list_result = [{**row[0]} for row in query_result]

        return template_list_result

    @classmethod
    async def add_template_services(cls, query_db: AsyncSession, page_object: TemplateBaseModel) -> CrudResponseModel:
        """
        新增用户信息service

        :param query_db: orm对象
        :param page_object: 新增用户对象
        :return: 新增用户校验结果
        """
        add_template = TemplateBaseModel(**page_object.model_dump(by_alias=True))
        add_template.update_time = int(datetime.now().timestamp() * 1000)
        if not await cls.check_template_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增消息模板{page_object.name}失败，模板名称已存在')
        try:
            await OaTemplateDao.add_template_dao(query_db, add_template)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def check_template_name_unique_services(cls, query_db: AsyncSession, page_object: TemplateBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        name = -1 if page_object.name is None else page_object.name
        template = await OaTemplateDao.get_template_by_info(query_db, TemplateBaseModel(name=page_object.name))
        if template and template.name == name:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def update_template_services(cls, query_db: AsyncSession, page_object: TemplateBaseModel) -> CrudResponseModel:
        """
        更新用户信息service

        :param query_db: orm对象
        :param page_object: 更新用户对象
        :return: 更新用户校验结果
        """
        update_template = TemplateBaseModel(**page_object.model_dump(by_alias=True))
        update_template.update_time=int(datetime.now().timestamp() * 1000)
        if not await cls.check_template_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'修改消息模板{page_object.name}失败，模板名称已存在')
        try:
            await OaTemplateDao.update_template_dao(query_db, update_template)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def detail_template_services(cls, query_db: AsyncSession, templateId: Integer) -> TemplateBaseModel | None:
        """
        获取用户详细信息service

        :param query_db: orm对象
        :param templateId: 模板id
        :return: 用户详细信息对象
        """
        try:
            if templateId:
                template = await OaTemplateDao.get_template_by_Id(query_db, templateId)
                return template
        except Exception as e:
            raise e

    @classmethod
    async def delete_template_services(cls, query_db: AsyncSession, templateId: Integer) -> TemplateBaseModel | None:
        """
        获取用户详细信息service

        :param query_db: orm对象
        :param templateId: 模板id
        :return: 用户详细信息对象
        """
        try:
            if templateId:
                template = await OaTemplateDao.delete_template_dao(query_db, templateId)
                return template
        except Exception as e:
            raise e
