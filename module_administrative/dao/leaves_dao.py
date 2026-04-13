from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_administrative.entity.do.leaves_do import OaLeaves
from module_administrative.entity.vo.leaves_vo import LeavesModel, LeavesPageQueryModel
from utils.page_util import PageUtil
from utils.log_util import logger


class LeavesDao:
    """
    请假管理模块数据库操作层
    """

    @classmethod
    async def get_leaves_detail_by_id(cls, db: AsyncSession, leaves_id: int) -> OaLeaves | None:
        """
        根据请假 id 获取请假详细信息

        :param db: orm 对象
        :param leaves_id: 请假 id
        :return: 请假信息对象
        """
        leaves_info = (
            (await db.execute(select(OaLeaves).where(OaLeaves.id == leaves_id)))
            .scalars()
            .first()
        )

        return leaves_info

    @classmethod
    async def get_leaves_list(
            cls, db: AsyncSession, query_object: LeavesPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取请假列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 请假列表信息对象
        """
        query = select(OaLeaves).where(
            OaLeaves.delete_time == 0,
            OaLeaves.admin_id == user_id
        )

        if query_object.keywords:
            query = query.where(
                OaLeaves.reason.like(f'%{query_object.keywords}%')
            )

        if query_object.types:
            query = query.where(OaLeaves.types == query_object.types)

        query = query.order_by(OaLeaves.create_time.desc()).distinct()

        leaves_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return leaves_list

    @classmethod
    async def add_leaves_dao(cls, db: AsyncSession, leaves: dict | LeavesModel) -> OaLeaves:
        """
        新增请假数据库操作

        :param db: orm 对象
        :param leaves: 请假对象或字典
        :return:
        """
        if isinstance(leaves, LeavesModel):
            leaves_dict = {
                k: v for k, v in leaves.model_dump().items()
                if k not in {'types_str', 'admin_name', 'dept_name'}
            }
        else:
            leaves_dict = leaves
        
        logger.info(f"DAO层接收到的数据 - admin_id: {leaves_dict.get('admin_id')}, did: {leaves_dict.get('did')}, types: {leaves_dict.get('types')}")
        
        db_leaves = OaLeaves(**leaves_dict)
        db.add(db_leaves)
        await db.flush()

        return db_leaves

    @classmethod
    async def edit_leaves_dao(cls, db: AsyncSession, leaves_id: int, leaves: dict) -> None:
        """
        编辑请假数据库操作

        :param db: orm 对象
        :param leaves_id: 请假 ID
        :param leaves: 需要更新的请假字典
        :return:
        """
        await db.execute(
            update(OaLeaves)
            .where(OaLeaves.id == leaves_id)
            .values(**leaves)
        )

    @classmethod
    async def delete_leaves_dao(cls, db: AsyncSession, leaves: LeavesModel) -> None:
        """
        删除请假数据库操作（逻辑删除）

        :param db: orm 对象
        :param leaves: 请假对象
        :return:
        """
        update_time = leaves.update_time if leaves.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaLeaves)
            .where(OaLeaves.id.in_([leaves.id]))
            .values(delete_time=delete_time, update_time=update_time)
        )