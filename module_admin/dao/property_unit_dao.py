from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_unit_do import SysPropertyUnit
from module_admin.entity.vo.property_unit_vo import PropertyUnitModel, PropertyUnitPageQueryModel
from utils.page_util import PageUtil


class PropertyUnitDao:
    """
    资产单位管理模块数据库操作层
    """

    @classmethod
    async def get_property_unit_detail_by_id(cls, db: AsyncSession, property_unit_id: int) -> SysPropertyUnit | None:
        """
        根据单位 ID 获取资产单位详细信息

        :param db: orm 对象
        :param property_unit_id: 单位 ID
        :return: 资产单位信息对象
        """
        property_unit_info = (
            (await db.execute(select(SysPropertyUnit).where(SysPropertyUnit.id == property_unit_id)))
            .scalars()
            .first()
        )

        return property_unit_info

    @classmethod
    async def get_property_unit_detail_by_info(cls, db: AsyncSession, property_unit: PropertyUnitModel) -> SysPropertyUnit | None:
        """
        根据资产单位参数获取信息

        :param db: orm 对象
        :param property_unit: 资产单位参数对象
        :return: 资产单位信息对象
        """
        query_conditions = []
        if property_unit.id is not None:
            query_conditions.append(SysPropertyUnit.id == property_unit.id)
        if property_unit.title:
            query_conditions.append(SysPropertyUnit.title == property_unit.title)

        if query_conditions:
            property_unit_info = (
                (await db.execute(select(SysPropertyUnit).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            property_unit_info = None

        return property_unit_info

    @classmethod
    async def get_property_unit_list(
            cls, db: AsyncSession, query_object: PropertyUnitPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取资产单位列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产单位列表信息对象
        """
        query = (
            select(SysPropertyUnit)
            .where(
                SysPropertyUnit.status != -1,
                SysPropertyUnit.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysPropertyUnit.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysPropertyUnit.sort.desc(), SysPropertyUnit.create_time.asc())
            .distinct()
        )
        property_unit_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return property_unit_list

    @classmethod
    async def get_all_property_unit_list(cls, db: AsyncSession) -> list[dict]:
        """
        获取所有资产单位列表信息

        :param db: orm 对象
        :return: 资产单位列表信息对象
        """
        query = (
            select(SysPropertyUnit)
            .where(SysPropertyUnit.status != -1)
            .order_by(SysPropertyUnit.sort.desc(), SysPropertyUnit.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_property_unit_dao(cls, db: AsyncSession, property_unit: PropertyUnitModel) -> SysPropertyUnit:
        """
        新增资产单位数据库操作

        :param db: orm 对象
        :param property_unit: 资产单位对象
        :return:
        """
        db_property_unit = SysPropertyUnit(**property_unit.model_dump())
        db.add(db_property_unit)
        await db.flush()

        return db_property_unit

    @classmethod
    async def edit_property_unit_dao(cls, db: AsyncSession, property_unit: dict) -> None:
        """
        编辑资产单位数据库操作

        :param db: orm 对象
        :param property_unit: 需要更新的资产单位字典
        :return:
        """
        await db.execute(update(SysPropertyUnit), [property_unit])

    @classmethod
    async def delete_property_unit_dao(cls, db: AsyncSession, property_unit: PropertyUnitModel) -> None:
        """
        删除资产单位数据库操作（逻辑删除）

        :param db: orm 对象
        :param property_unit: 资产单位对象
        :return:
        """
        update_time = property_unit.update_time if property_unit.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyUnit)
            .where(SysPropertyUnit.id == property_unit.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_property_unit_dao(cls, db: AsyncSession, property_unit: PropertyUnitModel) -> None:
        """
        禁用资产单位数据库操作

        :param db: orm 对象
        :param property_unit: 资产单位对象
        :return:
        """
        update_time = property_unit.update_time if property_unit.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyUnit)
            .where(SysPropertyUnit.id == property_unit.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_property_unit_dao(cls, db: AsyncSession, property_unit: PropertyUnitModel) -> None:
        """
        启用资产单位数据库操作

        :param db: orm 对象
        :param property_unit: 资产单位对象
        :return:
        """
        update_time = property_unit.update_time if property_unit.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyUnit)
            .where(SysPropertyUnit.id == property_unit.id)
            .values(status=1, update_time=update_time)
        )
