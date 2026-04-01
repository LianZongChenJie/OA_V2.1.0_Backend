from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_cate_do import SysPropertyCate
from module_admin.entity.vo.property_cate_vo import PropertyCateModel, PropertyCatePageQueryModel
from utils.page_util import PageUtil


class PropertyCateDao:
    """
    资产分类管理模块数据库操作层
    """

    @classmethod
    async def get_property_cate_detail_by_id(cls, db: AsyncSession, property_cate_id: int) -> SysPropertyCate | None:
        """
        根据分类 ID 获取资产分类详细信息

        :param db: orm 对象
        :param property_cate_id: 分类 ID
        :return: 资产分类信息对象
        """
        property_cate_info = (
            (await db.execute(select(SysPropertyCate).where(SysPropertyCate.id == property_cate_id)))
            .scalars()
            .first()
        )

        return property_cate_info

    @classmethod
    async def get_property_cate_detail_by_info(cls, db: AsyncSession, property_cate: PropertyCateModel) -> SysPropertyCate | None:
        """
        根据资产分类参数获取信息

        :param db: orm 对象
        :param property_cate: 资产分类参数对象
        :return: 资产分类信息对象
        """
        query_conditions = []
        if property_cate.id is not None:
            query_conditions.append(SysPropertyCate.id == property_cate.id)
        if property_cate.title:
            query_conditions.append(SysPropertyCate.title == property_cate.title)
        if property_cate.pid is not None:
            query_conditions.append(SysPropertyCate.pid == property_cate.pid)

        if query_conditions:
            property_cate_info = (
                (await db.execute(select(SysPropertyCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            property_cate_info = None

        return property_cate_info

    @classmethod
    async def get_property_cate_list(
            cls, db: AsyncSession, query_object: PropertyCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取资产分类列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产分类列表信息对象
        """
        query = (
            select(SysPropertyCate)
            .where(
                SysPropertyCate.status != -1,
                SysPropertyCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysPropertyCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysPropertyCate.sort.desc(), SysPropertyCate.create_time.asc())
            .distinct()
        )
        property_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return property_cate_list

    @classmethod
    async def get_property_cate_children_list(cls, db: AsyncSession, pid: int) -> list[dict[str, Any]]:
        """
        根据父分类 ID 获取子分类列表（用于树形结构的子节点查询）

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: 子分类列表信息对象
        """
        query = (
            select(SysPropertyCate)
            .where(
                SysPropertyCate.status != -1,
                SysPropertyCate.pid == pid
            )
            .order_by(SysPropertyCate.sort.desc(), SysPropertyCate.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def get_all_property_cate_list(cls, db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有资产分类列表信息（用于生成树形结构）

        :param db: orm 对象
        :return: 资产分类列表信息对象
        """
        query = (
            select(SysPropertyCate)
            .where(SysPropertyCate.status != -1)
            .order_by(SysPropertyCate.sort.desc(), SysPropertyCate.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_property_cate_dao(cls, db: AsyncSession, property_cate: PropertyCateModel) -> SysPropertyCate:
        """
        新增资产分类数据库操作

        :param db: orm 对象
        :param property_cate: 资产分类对象
        :return:
        """
        db_property_cate = SysPropertyCate(**property_cate.model_dump())
        db.add(db_property_cate)
        await db.flush()

        return db_property_cate

    @classmethod
    async def edit_property_cate_dao(cls, db: AsyncSession, property_cate: dict) -> None:
        """
        编辑资产分类数据库操作

        :param db: orm 对象
        :param property_cate: 需要更新的资产分类字典
        :return:
        """
        await db.execute(update(SysPropertyCate), [property_cate])

    @classmethod
    async def delete_property_cate_dao(cls, db: AsyncSession, property_cate: PropertyCateModel) -> None:
        """
        删除资产分类数据库操作（逻辑删除）

        :param db: orm 对象
        :param property_cate: 资产分类对象
        :return:
        """
        update_time = property_cate.update_time if property_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyCate)
            .where(SysPropertyCate.id == property_cate.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_property_cate_dao(cls, db: AsyncSession, property_cate: PropertyCateModel) -> None:
        """
        禁用资产分类数据库操作

        :param db: orm 对象
        :param property_cate: 资产分类对象
        :return:
        """
        update_time = property_cate.update_time if property_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyCate)
            .where(SysPropertyCate.id == property_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_property_cate_dao(cls, db: AsyncSession, property_cate: PropertyCateModel) -> None:
        """
        启用资产分类数据库操作

        :param db: orm 对象
        :param property_cate: 资产分类对象
        :return:
        """
        update_time = property_cate.update_time if property_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyCate)
            .where(SysPropertyCate.id == property_cate.id)
            .values(status=1, update_time=update_time)
        )

    @classmethod
    async def count_child_property_cate_dao(cls, db: AsyncSession, pid: int) -> int | None:
        """
        根据父分类 ID 统计子分类数量

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: 子分类数量
        """
        from sqlalchemy import func

        child_count = (
            await db.execute(select(func.count('*')).select_from(SysPropertyCate).where(SysPropertyCate.pid == pid))
        ).scalar()

        return child_count

