from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.care_cate_do import SysCareCate
from module_admin.entity.vo.care_cate_vo import CareCateModel, CareCatePageQueryModel
from utils.page_util import PageUtil


class CareCateDao:
    """
    关怀项目管理模块数据库操作层
    """

    @classmethod
    async def get_care_cate_detail_by_id(cls, db: AsyncSession, care_cate_id: int) -> SysCareCate | None:
        """
        根据关怀项目 id 获取关怀项目详细信息

        :param db: orm 对象
        :param care_cate_id: 关怀项目 id
        :return: 关怀项目信息对象
        """
        care_cate_info = (
            (await db.execute(select(SysCareCate).where(SysCareCate.id == care_cate_id)))
            .scalars()
            .first()
        )

        return care_cate_info

    @classmethod
    async def get_care_cate_detail_by_info(cls, db: AsyncSession, care_cate: CareCateModel) -> SysCareCate | None:
        """
        根据关怀项目参数获取关怀项目信息

        :param db: orm 对象
        :param care_cate: 关怀项目参数对象
        :return: 关怀项目信息对象
        """
        query_conditions = []
        if care_cate.id is not None:
            query_conditions.append(SysCareCate.id == care_cate.id)
        if care_cate.title:
            query_conditions.append(SysCareCate.title == care_cate.title)

        if query_conditions:
            care_cate_info = (
                (await db.execute(select(SysCareCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            care_cate_info = None

        return care_cate_info

    @classmethod
    async def get_care_cate_list(
            cls, db: AsyncSession, query_object: CareCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取关怀项目列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 关怀项目列表信息对象
        """
        query = (
            select(SysCareCate)
            .where(
                SysCareCate.status != -1,
                SysCareCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysCareCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysCareCate.id)
            .distinct()
        )
        care_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return care_cate_list

    @classmethod
    async def add_care_cate_dao(cls, db: AsyncSession, care_cate: CareCateModel) -> SysCareCate:
        """
        新增关怀项目数据库操作

        :param db: orm 对象
        :param care_cate: 关怀项目对象
        :return:
        """
        db_care_cate = SysCareCate(**care_cate.model_dump())
        db.add(db_care_cate)
        await db.flush()

        return db_care_cate

    @classmethod
    async def edit_care_cate_dao(cls, db: AsyncSession, care_cate: dict) -> None:
        """
        编辑关怀项目数据库操作

        :param db: orm 对象
        :param care_cate: 需要更新的关怀项目字典
        :return:
        """
        await db.execute(update(SysCareCate), [care_cate])

    @classmethod
    async def delete_care_cate_dao(cls, db: AsyncSession, care_cate: CareCateModel) -> None:
        """
        删除关怀项目数据库操作（逻辑删除）

        :param db: orm 对象
        :param care_cate: 关怀项目对象
        :return:
        """
        update_time = care_cate.update_time if care_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysCareCate)
            .where(SysCareCate.id.in_([care_cate.id]))
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_care_cate_dao(cls, db: AsyncSession, care_cate: CareCateModel) -> None:
        """
        禁用关怀项目数据库操作

        :param db: orm 对象
        :param care_cate: 关怀项目对象
        :return:
        """
        update_time = care_cate.update_time if care_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysCareCate)
            .where(SysCareCate.id == care_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_care_cate_dao(cls, db: AsyncSession, care_cate: CareCateModel) -> None:
        """
        启用关怀项目数据库操作

        :param db: orm 对象
        :param care_cate: 关怀项目对象
        :return:
        """
        update_time = care_cate.update_time if care_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysCareCate)
            .where(SysCareCate.id == care_cate.id)
            .values(status=1, update_time=update_time)
        )

