from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import ColumnElement, and_, delete, desc, func, or_, select, update
from typing import Any

from common.vo import PageModel
from module_admin.entity.vo.user_vo import UserPageQueryModel
from module_basicdata.entity.do.template_do import OaTemplate

from datetime import datetime, time

from module_basicdata.entity.vo.template_vo import TemplateBaseModel
from utils.page_util import PageUtil


class OaTemplateDao:
    @classmethod
    async def get_template_list(
        cls, db: AsyncSession, query_object: UserPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False
        ) -> PageModel | list[list[dict[str, Any]]]:
        """
        根据查询参数获取用户列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用模板表信息对象
        """
        query = (
            select(OaTemplate)
            .where(
                OaTemplate.status == '1'
                if query_object
                else True,
                OaTemplate.title.like(f'%{query_object.title}%') if query_object.title else True,
                OaTemplate.create_time.between(
                    datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                    datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)),
                )
                if query_object.begin_time and query_object.end_time
                else True,
                data_scope_sql,
            )
            .order_by(OaTemplate.create_time.desc())
        )
        template_list: PageModel | list[list[dict[str, Any]]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return template_list

    @classmethod
    async def add_template_dao(cls, db: AsyncSession, template: TemplateBaseModel) -> None:
        """
        新增用户角色关联信息数据库操作

        :param template:
        :param db: orm对象
        :return:
        """
        db_temp_role = OaTemplate(**template.model_dump())
        db.add(db_temp_role)

    @classmethod
    async def get_template_by_info(cls, db: AsyncSession, template: TemplateBaseModel) -> OaTemplate | None:
        """
        根据用户参数获取用户信息

        :param template:
        :param db: orm对象
        :return: 当前用户参数的用户信息对象
        """
        query_template_info = (
            (
                await db.execute(
                    select(OaTemplate)
                    .where(
                        OaTemplate.status == '1',
                        OaTemplate.name == template.name if template.name else True
                    )
                    .order_by(desc(OaTemplate.create_time))
                    .distinct()
                )
            )
            .scalars()
            .first()
        )

        return query_template_info