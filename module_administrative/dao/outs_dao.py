from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_administrative.entity.do.outs_do import OaOuts
from module_administrative.entity.vo.outs_vo import OutsModel, OutsPageQueryModel
from utils.page_util import PageUtil
from utils.log_util import logger


class OutsDao:
    """
    外出管理模块数据库操作层
    """

    @classmethod
    async def get_outs_detail_by_id(cls, db: AsyncSession, outs_id: int) -> OaOuts | None:
        """
        根据外出 id 获取外出详细信息

        :param db: orm 对象
        :param outs_id: 外出 id
        :return: 外出信息对象
        """
        outs_info = (
            (await db.execute(select(OaOuts).where(OaOuts.id == outs_id)))
            .scalars()
            .first()
        )

        return outs_info

    @classmethod
    async def get_outs_list(
            cls, db: AsyncSession, query_object: OutsPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取外出列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 外出列表信息对象
        """
        query = select(OaOuts).where(
            OaOuts.delete_time == 0,
            OaOuts.admin_id == user_id
        )

        if query_object.keywords:
            query = query.where(
                OaOuts.reason.like(f'%{query_object.keywords}%')
            )

        query = query.order_by(OaOuts.create_time.desc()).distinct()

        outs_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return outs_list

    @classmethod
    async def add_outs_dao(cls, db: AsyncSession, outs: dict | OutsModel) -> OaOuts:
        """
        新增外出数据库操作

        :param db: orm 对象
        :param outs: 外出对象或字典
        :return:
        """
        if isinstance(outs, OutsModel):
            outs_dict = {
                k: v for k, v in outs.model_dump().items()
                if k not in {'admin_name', 'dept_name'}
            }
        else:
            outs_dict = outs

        logger.info(f"DAO层接收到的外出数据 - admin_id: {outs_dict.get('admin_id')}, did: {outs_dict.get('did')}")

        db_outs = OaOuts(**outs_dict)
        db.add(db_outs)
        await db.flush()

        return db_outs

    @classmethod
    async def edit_outs_dao(cls, db: AsyncSession, outs_id: int, outs: dict) -> None:
        """
        编辑外出数据库操作

        :param db: orm 对象
        :param outs_id: 外出 ID
        :param outs: 需要更新的外出字典
        :return:
        """
        await db.execute(
            update(OaOuts)
            .where(OaOuts.id == outs_id)
            .values(**outs)
        )

    @classmethod
    async def delete_outs_dao(cls, db: AsyncSession, outs: OutsModel) -> None:
        """
        删除外出数据库操作（逻辑删除）

        :param db: orm 对象
        :param outs: 外出对象
        :return:
        """
        update_time = outs.update_time if outs.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaOuts)
            .where(OaOuts.id.in_([outs.id]))
            .values(delete_time=delete_time, update_time=update_time)
        )