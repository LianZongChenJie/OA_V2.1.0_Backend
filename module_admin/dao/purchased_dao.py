from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.purchased_do import OaPurchased
from module_admin.entity.do.purchased_cate_do import OaPurchasedCate
from module_admin.entity.vo.purchased_vo import PurchasedModel, PurchasedPageQueryModel
from utils.page_util import PageUtil


class PurchasedDao:
    """
    采购品管理模块数据库操作层
    """

    @classmethod
    async def get_purchased_detail_by_id(cls, db: AsyncSession, purchased_id: int) -> OaPurchased | None:
        """
        根据采购品 id 获取采购品详细信息

        :param db: orm 对象
        :param purchased_id: 采购品 id
        :return: 采购品信息对象
        """
        purchased_info = (
            (await db.execute(select(OaPurchased).where(OaPurchased.id == purchased_id)))
            .scalars()
            .first()
        )

        return purchased_info

    @classmethod
    async def get_purchased_detail_by_info(cls, db: AsyncSession, purchased: PurchasedModel) -> OaPurchased | None:
        """
        根据采购品参数获取采购品信息

        :param db: orm 对象
        :param purchased: 采购品参数对象
        :return: 采购品信息对象
        """
        query_conditions = []
        if purchased.title:
            query_conditions.append(OaPurchased.title == purchased.title)

        if query_conditions:
            purchased_info = (
                (await db.execute(select(OaPurchased).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            purchased_info = None

        return purchased_info

    @classmethod
    async def get_purchased_list(
            cls, db: AsyncSession, query_object: PurchasedPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取采购品列表信息（包含分类名称）

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 采购品列表信息对象
        """
        query = (
            select(
                OaPurchased,
                OaPurchasedCate.title.label('cate_name')
            )
            .outerjoin(OaPurchasedCate, OaPurchased.cate_id == OaPurchasedCate.id)
            .where(
                OaPurchased.delete_time == 0,
                OaPurchased.title.like(f'%{query_object.keywords}%') if query_object.keywords else True,
                OaPurchased.status == query_object.status if query_object.status is not None else True,
                OaPurchased.cate_id == query_object.cate_id if query_object.cate_id is not None else True,
                )
            .order_by(OaPurchased.create_time.desc())
            .distinct()
        )
        purchased_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return purchased_list

    @classmethod
    async def add_purchased_dao(cls, db: AsyncSession, purchased: PurchasedModel) -> OaPurchased:
        """
        新增采购品数据库操作

        :param db: orm 对象
        :param purchased: 采购品对象
        :return:
        """
        purchased_dict = purchased.model_dump(by_alias=False)
        db_purchased = OaPurchased(**purchased_dict)
        db.add(db_purchased)
        await db.flush()

        return db_purchased

    @classmethod
    async def edit_purchased_dao(cls, db: AsyncSession, purchased: dict) -> None:
        """
        编辑采购品数据库操作

        :param db: orm 对象
        :param purchased: 需要更新的采购品字典
        :return:
        """
        await db.execute(update(OaPurchased), [purchased])

    @classmethod
    async def delete_purchased_dao(cls, db: AsyncSession, purchased: PurchasedModel, del_type: int = 0) -> None:
        """
        删除采购品数据库操作（逻辑删除）

        :param db: orm 对象
        :param purchased: 采购品对象
        :param del_type: 删除类型
        :return:
        """
        update_time = purchased.update_time if purchased.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaPurchased)
            .where(OaPurchased.id.in_([purchased.id]))
            .values(status=-1, update_time=update_time, delete_time=delete_time)
        )

    @classmethod
    async def disable_purchased_dao(cls, db: AsyncSession, purchased: PurchasedModel) -> None:
        """
        禁用采购品数据库操作

        :param db: orm 对象
        :param purchased: 采购品对象
        :return:
        """
        update_time = purchased.update_time if purchased.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaPurchased)
            .where(OaPurchased.id == purchased.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_purchased_dao(cls, db: AsyncSession, purchased: PurchasedModel) -> None:
        """
        启用采购品数据库操作

        :param db: orm 对象
        :param purchased: 采购品对象
        :return:
        """
        update_time = purchased.update_time if purchased.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaPurchased)
            .where(OaPurchased.id == purchased.id)
            .values(status=1, update_time=update_time)
        )
