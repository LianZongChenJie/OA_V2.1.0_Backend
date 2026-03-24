from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.note_cate_do import SysNoteCate
from module_admin.entity.vo.note_cate_vo import NoteCateModel, NoteCatePageQueryModel
from utils.page_util import PageUtil


class NoteCateDao:
    """
    公告分类管理模块数据库操作层
    """

    @classmethod
    async def get_note_cate_detail_by_id(cls, db: AsyncSession, note_cate_id: int) -> SysNoteCate | None:
        """
        根据公告分类 id 获取公告分类详细信息

        :param db: orm 对象
        :param note_cate_id: 公告分类 id
        :return: 公告分类信息对象
        """
        note_cate_info = (
            (await db.execute(select(SysNoteCate).where(SysNoteCate.id == note_cate_id)))
            .scalars()
            .first()
        )

        return note_cate_info

    @classmethod
    async def get_note_cate_detail_by_info(cls, db: AsyncSession, note_cate: NoteCateModel) -> SysNoteCate | None:
        """
        根据公告分类参数获取公告分类信息

        :param db: orm 对象
        :param note_cate: 公告分类参数对象
        :return: 公告分类信息对象
        """
        query_conditions = []
        if note_cate.id is not None:
            query_conditions.append(SysNoteCate.id == note_cate.id)
        if note_cate.title:
            query_conditions.append(SysNoteCate.title == note_cate.title)

        if query_conditions:
            note_cate_info = (
                (await db.execute(select(SysNoteCate).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            note_cate_info = None

        return note_cate_info

    @classmethod
    async def get_note_cate_list(
            cls, db: AsyncSession, query_object: NoteCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取公告分类列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 公告分类列表信息对象
        """
        query = (
            select(SysNoteCate)
            .where(
                SysNoteCate.delete_time == 0,
                SysNoteCate.title.like(f'%{query_object.title}%') if query_object.title else True,
                SysNoteCate.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(SysNoteCate.sort)
            .distinct()
        )
        note_cate_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num if hasattr(query_object, 'page_num') else 1,
            query_object.page_size if hasattr(query_object, 'page_size') else 10, is_page
        )

        return note_cate_list

    @classmethod
    async def add_note_cate_dao(cls, db: AsyncSession, note_cate: NoteCateModel) -> SysNoteCate:
        """
        新增公告分类数据库操作

        :param db: orm 对象
        :param note_cate: 公告分类对象
        :return:
        """
        db_note_cate = SysNoteCate(**note_cate.model_dump())
        db.add(db_note_cate)
        await db.flush()

        return db_note_cate

    @classmethod
    async def edit_note_cate_dao(cls, db: AsyncSession, note_cate: dict) -> None:
        """
        编辑公告分类数据库操作

        :param db: orm 对象
        :param note_cate: 需要更新的公告分类字典
        :return:
        """
        await db.execute(update(SysNoteCate), [note_cate])

    @classmethod
    async def delete_note_cate_dao(cls, db: AsyncSession, note_cate: NoteCateModel) -> None:
        """
        删除公告分类数据库操作（逻辑删除）

        :param db: orm 对象
        :param note_cate: 公告分类对象
        :return:
        """
        update_time = note_cate.update_time if note_cate.update_time is not None else int(datetime.now().timestamp())
        
        await db.execute(
            update(SysNoteCate)
            .where(SysNoteCate.id == note_cate.id)
            .values(status=-1, update_time=update_time)
        )

    @classmethod
    async def disable_note_cate_dao(cls, db: AsyncSession, note_cate: NoteCateModel) -> None:
        """
        禁用公告分类数据库操作

        :param db: orm 对象
        :param note_cate: 公告分类对象
        :return:
        """
        update_time = note_cate.update_time if note_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysNoteCate)
            .where(SysNoteCate.id == note_cate.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_note_cate_dao(cls, db: AsyncSession, note_cate: NoteCateModel) -> None:
        """
        启用公告分类数据库操作

        :param db: orm 对象
        :param note_cate: 公告分类对象
        :return:
        """
        update_time = note_cate.update_time if note_cate.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(SysNoteCate)
            .where(SysNoteCate.id == note_cate.id)
            .values(status=1, update_time=update_time)
        )

