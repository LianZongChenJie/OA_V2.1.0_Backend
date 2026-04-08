"""
网盘分享空间管理模块数据库操作层
"""
import time
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_disk.entity.do.disk_do import OaDisk
from module_disk.entity.do.disk_group_do import OaDiskGroup
from module_disk.entity.vo.disk_group_vo import DiskGroupPageQueryModel
from utils.page_util import PageUtil


class DiskGroupDao:
    """
    网盘分享空间管理模块数据库操作层
    """

    @classmethod
    async def get_disk_group_detail_by_id(cls, db: AsyncSession, group_id: int) -> OaDiskGroup | None:
        """
        根据分享空间 id 获取详细信息

        :param db: orm 对象
        :param group_id: 分享空间 id
        :return: 分享空间信息对象
        """
        group_info = (
            (await db.execute(select(OaDiskGroup).where(OaDiskGroup.id == group_id)))
            .scalars()
            .first()
        )
        return group_info

    @classmethod
    async def get_disk_group_by_title(cls, db: AsyncSession, title: str, exclude_id: int = None) -> OaDiskGroup | None:
        """
        根据标题获取分享空间信息

        :param db: orm 对象
        :param title: 分享空间名称
        :param exclude_id: 排除的ID（编辑时使用）
        :return: 分享空间信息对象
        """
        conditions = [OaDiskGroup.delete_time == 0, OaDiskGroup.title == title]
        if exclude_id:
            conditions.append(OaDiskGroup.id != exclude_id)

        group_info = (
            (await db.execute(select(OaDiskGroup).where(and_(*conditions))))
            .scalars()
            .first()
        )
        return group_info

    @classmethod
    async def get_disk_group_list(
            cls, db: AsyncSession, query_object: DiskGroupPageQueryModel,
            where_conditions: list, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取分享空间列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param where_conditions: 查询条件列表
        :param is_page: 是否开启分页
        :return: 分享空间列表信息对象
        """
        query = select(OaDiskGroup).where(*where_conditions)
        query = query.order_by(OaDiskGroup.create_time.desc())

        group_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return group_list

    @classmethod
    async def add_disk_group_dao(cls, db: AsyncSession, group: OaDiskGroup) -> OaDiskGroup:
        """
        新增分享空间数据库操作

        :param db: orm 对象
        :param group: 分享空间对象
        :return:
        """
        db.add(group)
        await db.flush()
        return group

    @classmethod
    async def edit_disk_group_dao(cls, db: AsyncSession, group_id: int, group_data: dict) -> None:
        """
        编辑分享空间数据库操作

        :param db: orm 对象
        :param group_id: 分享空间ID
        :param group_data: 需要更新的分享空间数据
        :return:
        """
        await db.execute(
            update(OaDiskGroup)
            .where(OaDiskGroup.id == group_id)
            .values(**group_data)
        )

    @classmethod
    async def delete_disk_group_dao(cls, db: AsyncSession, group_id: int) -> None:
        """
        删除分享空间数据库操作

        :param db: orm 对象
        :param group_id: 分享空间ID
        :return:
        """
        await db.execute(
            update(OaDiskGroup)
            .where(OaDiskGroup.id == group_id)
            .values(delete_time=int(time.time()))
        )

    @classmethod
    async def get_group_disk_count(cls, db: AsyncSession, group_id: int) -> int:
        """
        获取分享空间中的文件数量

        :param db: orm 对象
        :param group_id: 分享空间ID
        :return: 文件数量
        """
        result = await db.execute(
            select(OaDisk)
            .where(OaDisk.group_id == group_id, OaDisk.delete_time == 0)
        )
        return len(result.scalars().all())
