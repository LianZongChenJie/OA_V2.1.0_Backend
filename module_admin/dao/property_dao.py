from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_do import OaProperty as SysProperty
from module_admin.entity.vo.property_vo import PropertyModel, PropertyPageQueryModel
from utils.page_util import PageUtil

class PropertyDao:
    """
    资产管理模块数据库操作层
    """

    @classmethod
    async def get_property_detail_by_id(cls, db: AsyncSession, property_id: int) -> SysProperty | None:
        """
        根据资产 ID 获取资产详细信息

        :param db: orm 对象
        :param property_id: 资产 ID
        :return: 资产信息对象
        """
        property_info = (
            (await db.execute(select(SysProperty).where(SysProperty.id == property_id)))
            .scalars()
            .first()
        )

        return property_info

    @classmethod
    async def get_property_detail_by_info(cls, db: AsyncSession, property: PropertyModel) -> SysProperty | None:
        """
        根据资产参数获取信息

        :param db: orm 对象
        :param property: 资产参数对象
        :return: 资产信息对象
        """
        query_conditions = []
        if property.title:
            query_conditions.append(SysProperty.title == property.title)

        if query_conditions:
            property_info = (
                (await db.execute(select(SysProperty).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            property_info = None

        return property_info

    @classmethod
    async def get_property_list(
            cls, db: AsyncSession, query_object: PropertyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取资产列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产列表信息对象
        """
        query = (
            select(SysProperty)
            .where(
                SysProperty.status != -1,
                SysProperty.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysProperty.code.like(f'%{query_object.code}%') if query_object.code else True,
                SysProperty.cate_id == query_object.cate_id if query_object.cate_id is not None else True,
                SysProperty.brand_id == query_object.brand_id if query_object.brand_id is not None else True,
                SysProperty.unit_id == query_object.unit_id if query_object.unit_id is not None else True,
                SysProperty.status == query_object.status if query_object.status is not None else True,
                SysProperty.source == query_object.source if query_object.source is not None else True,
            )
            .order_by(SysProperty.create_time.desc())
            .distinct()
        )
        property_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return property_list

    @classmethod
    async def get_all_property_list(cls, db: AsyncSession) -> list[dict]:
        """
        获取所有资产列表信息

        :param db: orm 对象
        :return: 资产列表信息对象
        """
        query = (
            select(SysProperty)
            .where(SysProperty.status != -1)
            .order_by(SysProperty.create_time.desc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_property_dao(cls, db: AsyncSession, property: PropertyModel) -> SysProperty:
        """
        新增资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        property_data = property.model_dump()
        # Pydantic 使用 model_ 避免与保留字冲突，需要转换为数据库字段 model
        if 'model_' in property_data:
            property_data['model'] = property_data.pop('model_')
        
        db_property = SysProperty(**property_data)
        db.add(db_property)
        await db.flush()

        return db_property

    @classmethod
    async def edit_property_dao(cls, db: AsyncSession, property: dict) -> None:
        """
        编辑资产数据库操作

        :param db: orm 对象
        :param property: 需要更新的资产字典
        :return:
        """
        await db.execute(update(SysProperty), [property])

    @classmethod
    async def delete_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        删除资产数据库操作（逻辑删除）

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        禁用资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_property_dao(cls, db: AsyncSession, property: PropertyModel) -> None:
        """
        启用资产数据库操作

        :param db: orm 对象
        :param property: 资产对象
        :return:
        """
        update_time = property.update_time if property.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysProperty)
            .where(SysProperty.id == property.id)
            .values(status=1, update_time=update_time)
        )