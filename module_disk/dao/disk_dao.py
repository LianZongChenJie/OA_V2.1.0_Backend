"""
网盘文件管理模块数据库操作层
"""
from typing import Any

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_disk.entity.do.disk_do import OaDisk
from module_disk.entity.vo.disk_vo import DiskPageQueryModel
from utils.page_util import PageUtil


class DiskDao:
    """
    网盘文件管理模块数据库操作层
    """

    @classmethod
    async def get_disk_detail_by_id(cls, db: AsyncSession, disk_id: int) -> OaDisk | None:
        """
        根据文件 id 获取文件详细信息

        :param db: orm 对象
        :param disk_id: 文件 id
        :return: 文件信息对象
        """
        disk_info = (
            (await db.execute(select(OaDisk).where(OaDisk.id == disk_id)))
            .scalars()
            .first()
        )
        return disk_info

    @classmethod
    async def get_disk_list(
            cls, db: AsyncSession, query_object: DiskPageQueryModel,
            where_conditions: list, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取网盘文件列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param where_conditions: 查询条件列表
        :param is_page: 是否开启分页
        :return: 网盘文件列表信息对象
        """
        query = select(OaDisk).where(*where_conditions)
        query = query.order_by(OaDisk.create_time.desc())

        disk_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return disk_list

    @classmethod
    async def add_disk_dao(cls, db: AsyncSession, disk: OaDisk) -> OaDisk:
        """
        新增网盘文件数据库操作

        :param db: orm 对象
        :param disk: 文件对象
        :return:
        """
        db.add(disk)
        await db.flush()
        return disk

    @classmethod
    async def edit_disk_dao(cls, db: AsyncSession, disk_id: int, disk_data: dict) -> None:
        """
        编辑网盘文件数据库操作

        :param db: orm 对象
        :param disk_id: 文件ID
        :param disk_data: 需要更新的文件数据
        :return:
        """
        await db.execute(
            update(OaDisk)
            .where(OaDisk.id == disk_id)
            .values(**disk_data)
        )

    @classmethod
    async def batch_update_disk_dao(cls, db: AsyncSession, update_list: list[dict]) -> None:
        """
        批量更新网盘文件数据库操作

        :param db: orm 对象
        :param update_list: 更新数据列表
        :return:
        """
        for item in update_list:
            disk_id = item.pop('id')
            await db.execute(
                update(OaDisk)
                .where(OaDisk.id == disk_id)
                .values(**item)
            )

    @classmethod
    async def get_child_disk_count(cls, db: AsyncSession, pid: int) -> int:
        """
        获取子文件数量

        :param db: orm 对象
        :param pid: 父文件夹ID
        :return: 子文件数量
        """
        result = await db.execute(
            select(OaDisk)
            .where(OaDisk.pid == pid, OaDisk.delete_time == 0)
        )
        return len(result.scalars().all())

    @classmethod
    async def get_parent_ids(cls, db: AsyncSession, disk_id: int) -> list[int]:
        """
        获取所有父级文件夹ID

        :param db: orm 对象
        :param disk_id: 文件ID
        :return: 父级ID列表
        """
        parent_ids = []
        current_id = disk_id

        while current_id > 0:
            disk = await cls.get_disk_detail_by_id(db, current_id)
            if disk and disk.pid > 0:
                parent_ids.append(disk.id)
                current_id = disk.pid
            else:
                break

        return parent_ids
