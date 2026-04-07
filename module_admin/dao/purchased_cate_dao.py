from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.purchased_cate_do import OaPurchasedCate
from module_admin.entity.vo.purchased_cate_vo import PurchasedCateModel, PurchasedCatePageQueryModel, PurchasedCateTreeModel
from utils.page_util import PageUtil


class PurchasedCateDao:
    """
    采购品分类管理模块数据库操作层
    """

    @classmethod
    async def get_purchased_cate_detail_by_id(cls, db: AsyncSession, cate_id: int) -> OaPurchasedCate | None:
        """
        根据分类 id 获取分类详细信息

        :param db: orm 对象
        :param cate_id: 分类 id
        :return: 分类信息对象
        """
        cate_info = (
            (await db.execute(select(OaPurchasedCate).where(OaPurchasedCate.id == cate_id)))
            .scalars()
            .first()
        )

        return cate_info

    @classmethod
    async def get_purchased_cate_detail_by_info(cls, db: AsyncSession, cate: PurchasedCateModel) -> OaPurchasedCate | None:
        """
        根据分类参数获取分类信息

        :param db: orm 对象
        :param cate: 分类参数对象
        :return: 分类信息对象
        """
        query_conditions = []
        if cate.id is not None:
            query_conditions.append(OaPurchasedCate.id == cate.id)
        if cate.title:
            query_conditions.append(OaPurchasedCate.title == cate.title)

        if query_conditions:
            cate_info = (
                (await db.execute(select(OaPurchasedCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            cate_info = None

        return cate_info

    @classmethod
    async def get_purchased_cate_list(
            cls, db: AsyncSession, query_object: PurchasedCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取分类列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 分类列表信息对象
        """
        query = (
            select(OaPurchasedCate)
            .where(
                OaPurchasedCate.status != -1,
                OaPurchasedCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                OaPurchasedCate.status == query_object.status if query_object.status is not None else True,
                OaPurchasedCate.pid == query_object.pid if query_object.pid is not None else True,
                )
            .order_by(OaPurchasedCate.sort.desc(), OaPurchasedCate.create_time.asc())
            .distinct()
        )
        purchased_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return purchased_cate_list

    @classmethod
    async def get_all_purchased_cate_list(cls, db: AsyncSession) -> list[OaPurchasedCate]:
        """
        获取所有分类列表（用于生成树形结构）

        :param db: orm 对象
        :return: 分类列表对象
        """
        query = (
            select(OaPurchasedCate)
            .where(OaPurchasedCate.status != -1)
            .order_by(OaPurchasedCate.sort.desc(), OaPurchasedCate.create_time.asc())
        )
        result = (await db.execute(query)).scalars().all()

        return result

    @classmethod
    async def get_purchased_cate_children_list(cls, db: AsyncSession, pid: int) -> list[dict[str, Any]]:
        """
        根据父分类 ID 获取子分类列表（用于树形结构的子节点查询）

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: 子分类列表信息对象
        """
        query = (
            select(OaPurchasedCate)
            .where(
                OaPurchasedCate.status != -1,
                OaPurchasedCate.pid == pid
            )
            .order_by(OaPurchasedCate.sort.desc(), OaPurchasedCate.create_time.asc())
            .distinct()
        )
        result = (await db.execute(query)).scalars().all()

        return [item.__dict__ for item in result if not getattr(item, '_sa_instance_state').deleted]

    @classmethod
    async def add_purchased_cate_dao(cls, db: AsyncSession, cate: PurchasedCateModel) -> OaPurchasedCate:
        """
        新增分类数据库操作

        :param db: orm 对象
        :param cate: 分类对象
        :return:
        """
        cate_dict = cate.model_dump(by_alias=False)
        db_cate = OaPurchasedCate(**cate_dict)
        db.add(db_cate)
        await db.flush()

        return db_cate

    @classmethod
    async def edit_purchased_cate_dao(cls, db: AsyncSession, cate: dict) -> None:
        """
        编辑分类数据库操作

        :param db: orm 对象
        :param cate: 需要更新的分类字典
        :return:
        """
        await db.execute(update(OaPurchasedCate), [cate])

    @classmethod
    async def delete_purchased_cate_dao(cls, db: AsyncSession, cate_id: int) -> None:
        """
        删除分类数据库操作（逻辑删除）

        :param db: orm 对象
        :param cate_id: 分类 id
        :return:
        """
        update_time = int(datetime.now().timestamp())
        await db.execute(
            update(OaPurchasedCate)
            .where(OaPurchasedCate.id == cate_id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_purchased_cate_dao(cls, db: AsyncSession, cate: PurchasedCateModel) -> None:
        """
        禁用分类数据库操作

        :param db: orm 对象
        :param cate: 分类对象
        :return:
        """
        update_time = cate.update_time if cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaPurchasedCate)
            .where(OaPurchasedCate.id == cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_purchased_cate_dao(cls, db: AsyncSession, cate: PurchasedCateModel) -> None:
        """
        启用分类数据库操作

        :param db: orm 对象
        :param cate: 分类对象
        :return:
        """
        update_time = cate.update_time if cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaPurchasedCate)
            .where(OaPurchasedCate.id == cate.id)
            .values(status=1, update_time=update_time)
        )

    @classmethod
    async def has_children(cls, db: AsyncSession, pid: int) -> bool:
        """
        检查是否有子分类

        :param db: orm 对象
        :param pid: 父分类 ID
        :return: True 如果有子分类，否则 False
        """
        query = select(OaPurchasedCate.id).where(
            OaPurchasedCate.pid == pid,
            OaPurchasedCate.status != -1
        )
        result = (await db.execute(query)).scalars().first()
        return result is not None
