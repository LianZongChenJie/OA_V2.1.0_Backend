from datetime import datetime

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.property_brand_do import SysPropertyBrand
from module_admin.entity.vo.property_brand_vo import PropertyBrandModel, PropertyBrandPageQueryModel
from utils.page_util import PageUtil


class PropertyBrandDao:
    """
    资产品牌管理模块数据库操作层
    """

    @classmethod
    async def get_property_brand_detail_by_id(cls, db: AsyncSession, property_brand_id: int) -> SysPropertyBrand | None:
        """
        根据品牌 ID 获取资产品牌详细信息

        :param db: orm 对象
        :param property_brand_id: 品牌 ID
        :return: 资产品牌信息对象
        """
        property_brand_info = (
            (await db.execute(select(SysPropertyBrand).where(SysPropertyBrand.id == property_brand_id)))
            .scalars()
            .first()
        )

        return property_brand_info

    @classmethod
    async def get_property_brand_detail_by_info(cls, db: AsyncSession, property_brand: PropertyBrandModel) -> SysPropertyBrand | None:
        """
        根据资产品牌参数获取信息

        :param db: orm 对象
        :param property_brand: 资产品牌参数对象
        :return: 资产品牌信息对象
        """
        query_conditions = []
        if property_brand.id is not None:
            query_conditions.append(SysPropertyBrand.id == property_brand.id)
        if property_brand.title:
            query_conditions.append(SysPropertyBrand.title == property_brand.title)

        if query_conditions:
            property_brand_info = (
                (await db.execute(select(SysPropertyBrand).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            property_brand_info = None

        return property_brand_info

    @classmethod
    async def get_property_brand_list(
            cls, db: AsyncSession, query_object: PropertyBrandPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取资产品牌列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 资产品牌列表信息对象
        """
        query = (
            select(SysPropertyBrand)
            .where(
                SysPropertyBrand.status != -1,
                SysPropertyBrand.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysPropertyBrand.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysPropertyBrand.sort.desc(), SysPropertyBrand.create_time.asc())
            .distinct()
        )
        property_brand_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return property_brand_list

    @classmethod
    async def get_all_property_brand_list(cls, db: AsyncSession) -> list[dict]:
        """
        获取所有资产品牌列表信息

        :param db: orm 对象
        :return: 资产品牌列表信息对象
        """
        query = (
            select(SysPropertyBrand)
            .where(SysPropertyBrand.status != -1)
            .order_by(SysPropertyBrand.sort.desc(), SysPropertyBrand.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not item._sa_instance_state.deleted]

    @classmethod
    async def add_property_brand_dao(cls, db: AsyncSession, property_brand: PropertyBrandModel) -> SysPropertyBrand:
        """
        新增资产品牌数据库操作

        :param db: orm 对象
        :param property_brand: 资产品牌对象
        :return:
        """
        db_property_brand = SysPropertyBrand(**property_brand.model_dump())
        db.add(db_property_brand)
        await db.flush()

        return db_property_brand

    @classmethod
    async def edit_property_brand_dao(cls, db: AsyncSession, property_brand: dict) -> None:
        """
        编辑资产品牌数据库操作

        :param db: orm 对象
        :param property_brand: 需要更新的资产品牌字典
        :return:
        """
        await db.execute(update(SysPropertyBrand), [property_brand])

    @classmethod
    async def delete_property_brand_dao(cls, db: AsyncSession, property_brand: PropertyBrandModel) -> None:
        """
        删除资产品牌数据库操作（逻辑删除）

        :param db: orm 对象
        :param property_brand: 资产品牌对象
        :return:
        """
        update_time = property_brand.update_time if property_brand.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyBrand)
            .where(SysPropertyBrand.id == property_brand.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_property_brand_dao(cls, db: AsyncSession, property_brand: PropertyBrandModel) -> None:
        """
        禁用资产品牌数据库操作

        :param db: orm 对象
        :param property_brand: 资产品牌对象
        :return:
        """
        update_time = property_brand.update_time if property_brand.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyBrand)
            .where(SysPropertyBrand.id == property_brand.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_property_brand_dao(cls, db: AsyncSession, property_brand: PropertyBrandModel) -> None:
        """
        启用资产品牌数据库操作

        :param db: orm 对象
        :param property_brand: 资产品牌对象
        :return:
        """
        update_time = property_brand.update_time if property_brand.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysPropertyBrand)
            .where(SysPropertyBrand.id == property_brand.id)
            .values(status=1, update_time=update_time)
        )
