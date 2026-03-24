from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.services_do import OaServices
from module_admin.entity.vo.services_vo import ServicesModel, ServicesPageQueryModel
from utils.page_util import PageUtil


class ServicesDao:
    """
    服务管理模块数据库操作层
    """

    @classmethod
    async def get_services_detail_by_id(cls, db: AsyncSession, services_id: int) -> OaServices | None:
        """
        根据服务 id 获取服务详细信息

        :param db: orm 对象
        :param services_id: 服务 id
        :return: 服务信息对象
        """
        services_info = (
            (await db.execute(select(OaServices).where(OaServices.id == services_id)))
            .scalars()
            .first()
        )

        return services_info

    @classmethod
    async def get_services_detail_by_info(cls, db: AsyncSession, services: ServicesModel) -> OaServices | None:
        """
        根据服务参数获取服务信息

        :param db: orm 对象
        :param services: 服务参数对象
        :return: 服务信息对象
        """
        query_conditions = []
        if services.title:
            query_conditions.append(OaServices.title == services.title)

        if query_conditions:
            services_info = (
                (await db.execute(select(OaServices).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            services_info = None

        return services_info

    @classmethod
    async def get_services_list(
            cls, db: AsyncSession, query_object: ServicesPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取服务列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 服务列表信息对象
        """
        query = (
            select(OaServices)
            .where(
                OaServices.delete_time == 0,
                OaServices.title.like(f'%{query_object.title}%') if query_object.title else True,
                OaServices.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(OaServices.sort.asc(), OaServices.id)
            .distinct()
        )
        services_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return services_list

    @classmethod
    async def add_services_dao(cls, db: AsyncSession, services: ServicesModel) -> OaServices:
        """
        新增服务数据库操作

        :param db: orm 对象
        :param services: 服务对象
        :return:
        """
        services_dict = services.model_dump(by_alias=False)
        db_services = OaServices(**services_dict)
        db.add(db_services)
        await db.flush()

        return db_services

    @classmethod
    async def edit_services_dao(cls, db: AsyncSession, services: dict) -> None:
        """
        编辑服务数据库操作

        :param db: orm 对象
        :param services: 需要更新的服务字典
        :return:
        """
        await db.execute(update(OaServices), [services])

    @classmethod
    async def delete_services_dao(cls, db: AsyncSession, services: ServicesModel, del_type: int = 0) -> None:
        """
        删除服务数据库操作（逻辑删除）

        :param db: orm 对象
        :param services: 服务对象
        :param del_type: 删除类型
        :return:
        """
        update_time = services.update_time if services.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaServices)
            .where(OaServices.id.in_([services.id]))
            .values(status=-1, update_time=update_time, delete_time=delete_time)
        )

    @classmethod
    async def disable_services_dao(cls, db: AsyncSession, services: ServicesModel) -> None:
        """
        禁用服务数据库操作

        :param db: orm 对象
        :param services: 服务对象
        :return:
        """
        update_time = services.update_time if services.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaServices)
            .where(OaServices.id == services.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_services_dao(cls, db: AsyncSession, services: ServicesModel) -> None:
        """
        启用服务数据库操作

        :param db: orm 对象
        :param services: 服务对象
        :return:
        """
        update_time = services.update_time if services.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaServices)
            .where(OaServices.id == services.id)
            .values(status=1, update_time=update_time)
        )
