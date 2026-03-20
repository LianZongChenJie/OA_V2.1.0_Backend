from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.supplier_do import OaSupplier
from module_admin.entity.vo.supplier_vo import SupplierModel, SupplierPageQueryModel
from utils.page_util import PageUtil


class SupplierDao:
    """
    供应商管理模块数据库操作层
    """

    @classmethod
    async def get_supplier_detail_by_id(cls, db: AsyncSession, supplier_id: int) -> OaSupplier | None:
        """
        根据供应商 id 获取供应商详细信息

        :param db: orm 对象
        :param supplier_id: 供应商 id
        :return: 供应商信息对象
        """
        supplier_info = (
            (await db.execute(select(OaSupplier).where(OaSupplier.id == supplier_id)))
            .scalars()
            .first()
        )

        return supplier_info

    @classmethod
    async def get_supplier_detail_by_info(cls, db: AsyncSession, supplier: SupplierModel) -> OaSupplier | None:
        """
        根据供应商参数获取供应商信息

        :param db: orm 对象
        :param supplier: 供应商参数对象
        :return: 供应商信息对象
        """
        query_conditions = []
        if supplier.id is not None:
            query_conditions.append(OaSupplier.id == supplier.id)
        if supplier.title:
            query_conditions.append(OaSupplier.title == supplier.title)

        if query_conditions:
            supplier_info = (
                (await db.execute(select(OaSupplier).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            supplier_info = None

        return supplier_info

    @classmethod
    async def get_supplier_list(
            cls, db: AsyncSession, query_object: SupplierPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取供应商列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 供应商列表信息对象
        """
        query = (
            select(OaSupplier)
            .where(
                OaSupplier.delete_time == 0,
                (OaSupplier.id.like(f'%{query_object.keywords}%') |
                 OaSupplier.title.like(f'%{query_object.keywords}%')) if query_object.keywords else True,
                OaSupplier.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(OaSupplier.sort.asc(), OaSupplier.create_time.desc())
            .distinct()
        )
        supplier_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return supplier_list

    @classmethod
    async def add_supplier_dao(cls, db: AsyncSession, supplier: SupplierModel) -> OaSupplier:
        """
        新增供应商数据库操作

        :param db: orm 对象
        :param supplier: 供应商对象
        :return:
        """
        supplier_dict = supplier.model_dump(by_alias=False)
        db_supplier = OaSupplier(**supplier_dict)
        db.add(db_supplier)
        await db.flush()

        return db_supplier

    @classmethod
    async def edit_supplier_dao(cls, db: AsyncSession, supplier: dict) -> None:
        """
        编辑供应商数据库操作

        :param db: orm 对象
        :param supplier: 需要更新的供应商字典
        :return:
        """
        await db.execute(update(OaSupplier), [supplier])

    @classmethod
    async def delete_supplier_dao(cls, db: AsyncSession, supplier: SupplierModel, del_type: int = 0) -> None:
        """
        删除供应商数据库操作（逻辑删除）

        :param db: orm 对象
        :param supplier: 供应商对象
        :param del_type: 删除类型
        :return:
        """
        update_time = supplier.update_time if supplier.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaSupplier)
            .where(OaSupplier.id.in_([supplier.id]))
            .values(status=-1, update_time=update_time, delete_time=delete_time)
        )

    @classmethod
    async def disable_supplier_dao(cls, db: AsyncSession, supplier: SupplierModel) -> None:
        """
        禁用供应商数据库操作

        :param db: orm 对象
        :param supplier: 供应商对象
        :return:
        """
        update_time = supplier.update_time if supplier.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaSupplier)
            .where(OaSupplier.id == supplier.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_supplier_dao(cls, db: AsyncSession, supplier: SupplierModel) -> None:
        """
        启用供应商数据库操作

        :param db: orm 对象
        :param supplier: 供应商对象
        :return:
        """
        update_time = supplier.update_time if supplier.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaSupplier)
            .where(OaSupplier.id == supplier.id)
            .values(status=1, update_time=update_time)
        )
