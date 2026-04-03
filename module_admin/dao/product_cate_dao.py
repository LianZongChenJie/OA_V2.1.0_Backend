from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.product_cate_do import OaProductCate
from module_admin.entity.vo.product_cate_vo import ProductCateModel, ProductCatePageQueryModel
from utils.page_util import PageUtil


class ProductCateDao:
    """
    产品分类管理模块数据库操作层
    """

    @classmethod
    async def get_product_cate_detail_by_id(cls, db: AsyncSession, product_cate_id: int) -> OaProductCate | None:
        """
        根据分类 ID 获取产品分类详细信息

        :param db: orm 对象
        :param product_cate_id: 分类 ID
        :return: 产品信息对象
        """
        product_cate_info = (
            (await db.execute(select(OaProductCate).where(OaProductCate.id == product_cate_id)))
            .scalars()
            .first()
        )

        return product_cate_info

    @classmethod
    async def get_product_cate_detail_by_info(cls, db: AsyncSession, product_cate: ProductCateModel) -> OaProductCate | None:
        """
        根据产品参数获取信息

        :param db: orm 对象
        :param product_cate: 产品参数对象
        :return: 产品信息对象
        """
        query_conditions = []
        if product_cate.title:
            query_conditions.append(OaProductCate.title == product_cate.title)

        if query_conditions:
            product_cate_info = (
                (await db.execute(select(OaProductCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            product_cate_info = None

        return product_cate_info

    @classmethod
    async def get_product_cate_list(
            cls, db: AsyncSession, query_object: ProductCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取产品列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品列表信息对象
        """
        query = (
            select(OaProductCate)
            .where(
                OaProductCate.status != -1,
                OaProductCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                OaProductCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(OaProductCate.sort.desc(), OaProductCate.create_time.asc())
            .distinct()
        )
        product_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return product_cate_list

    @classmethod
    async def get_all_product_cate_list(cls, db: AsyncSession) -> list[dict[str, Any]]:
        """
        获取所有产品分类列表信息（用于生成树形结构）

        :param db: orm 对象
        :return: 产品列表信息对象
        """
        query = (
            select(OaProductCate)
            .where(OaProductCate.status != -1)
            .order_by(OaProductCate.sort.desc(), OaProductCate.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not getattr(item, '_sa_instance_state').deleted]

    @classmethod
    async def get_product_cate_children_list(cls, db: AsyncSession, pid: int) -> list[dict[str, Any]]:
        """
        根据父分类 ID 获取子分类列表（用于树形结构的子节点查询）

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: 子分类列表信息对象
        """
        query = (
            select(OaProductCate)
            .where(
                OaProductCate.status != -1,
                OaProductCate.pid == pid
            )
            .order_by(OaProductCate.sort.desc(), OaProductCate.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not getattr(item, '_sa_instance_state').deleted]

    @classmethod
    async def add_product_cate_dao(cls, db: AsyncSession, product_cate: ProductCateModel) -> OaProductCate:
        """
        新增产品分类数据库操作

        :param db: orm 对象
        :param product_cate: 产品分类对象
        :return:
        """
        db_product_cate = OaProductCate(**product_cate.model_dump())
        db.add(db_product_cate)
        await db.flush()

        return db_product_cate

    @classmethod
    async def edit_product_cate_dao(cls, db: AsyncSession, product_cate: dict) -> None:
        """
        编辑产品分类数据库操作

        :param db: orm 对象
        :param product_cate: 需要更新的产品分类字典
        :return:
        """
        await db.execute(update(OaProductCate), [product_cate])

    @classmethod
    async def delete_product_cate_dao(cls, db: AsyncSession, product_cate: ProductCateModel) -> None:
        """
        删除产品分类数据库操作（逻辑删除）

        :param db: orm 对象
        :param product_cate: 产品分类对象
        :return:
        """
        update_time = product_cate.update_time if product_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProductCate)
            .where(OaProductCate.id == product_cate.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_product_cate_dao(cls, db: AsyncSession, product_cate: ProductCateModel) -> None:
        """
        禁用产品分类数据库操作

        :param db: orm 对象
        :param product_cate: 产品分类对象
        :return:
        """
        update_time = product_cate.update_time if product_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProductCate)
            .where(OaProductCate.id == product_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_product_cate_dao(cls, db: AsyncSession, product_cate: ProductCateModel) -> None:
        """
        启用产品分类数据库操作

        :param db: orm 对象
        :param product_cate: 产品分类对象
        :return:
        """
        update_time = product_cate.update_time if product_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProductCate)
            .where(OaProductCate.id == product_cate.id)
            .values(status=1, update_time=update_time)
        )

    @classmethod
    async def count_child_product_cate_dao(cls, db: AsyncSession, pid: int) -> int | None:
        """
        根据父分类 ID 统计子分类数量

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: 子分类数量
        """
        child_count = (
            await db.execute(select(func.count('*')).select_from(OaProductCate).where(OaProductCate.pid == pid))
        ).scalar()

        return child_count

