from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_contract.entity.do.purchase_do import OaPurchase
from module_contract.entity.vo.purchase_vo import PurchasePageQueryModel
from utils.page_util import PageUtil


class PurchaseDao:
    """
    采购合同管理模块数据库操作层
    """

    @classmethod
    async def get_purchase_list(
            cls, db: AsyncSession, query_object: PurchasePageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取采购合同列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 采购合同列表信息对象
        """
        # 基础条件：未删除
        conditions = [OaPurchase.delete_time == 0]

        # 根据状态标志设置不同的查询条件
        if hasattr(query_object, 'archive_status') and query_object.archive_status == 1:
            # 已归档采购合同
            conditions.append(OaPurchase.archive_time > 0)
        elif hasattr(query_object, 'stop_status') and query_object.stop_status == 1:
            # 已中止采购合同
            conditions.append(OaPurchase.stop_time > 0)
        elif hasattr(query_object, 'void_status') and query_object.void_status == 1:
            # 已作废采购合同
            conditions.append(OaPurchase.void_time > 0)
        else:
            # 正常采购合同：未归档、未中止、未作废
            conditions.append(OaPurchase.archive_time == 0)
            conditions.append(OaPurchase.stop_time == 0)
            conditions.append(OaPurchase.void_time == 0)

        # 关键词搜索
        if query_object.keywords:
            conditions.append(
                or_(
                    OaPurchase.id.like(f'%{query_object.keywords}%'),
                    OaPurchase.name.like(f'%{query_object.keywords}%'),
                    OaPurchase.code.like(f'%{query_object.keywords}%')
                )
            )

        # 合同性质筛选
        if query_object.types_filter is not None:
            conditions.append(OaPurchase.types == query_object.types_filter)

        # 分类筛选
        if query_object.cate_id_filter is not None:
            conditions.append(OaPurchase.cate_id == query_object.cate_id_filter)

        # 审核状态筛选
        if query_object.check_status_filter is not None:
            conditions.append(OaPurchase.check_status == query_object.check_status_filter)

        # 签订时间范围
        if query_object.sign_time_start is not None:
            conditions.append(OaPurchase.sign_time >= query_object.sign_time_start)
        if query_object.sign_time_end is not None:
            conditions.append(OaPurchase.sign_time <= query_object.sign_time_end)

        # 结束时间范围
        if query_object.end_time_start is not None:
            conditions.append(OaPurchase.end_time >= query_object.end_time_start)
        if query_object.end_time_end is not None:
            conditions.append(OaPurchase.end_time <= query_object.end_time_end)

        # 根据 tab 参数设置查询条件
        if query_object.tab == 0:
            # 全部采购合同（根据权限过滤）
            if query_object.admin_id_filter is not None:
                conditions.append(OaPurchase.sign_uid == query_object.admin_id_filter)
        elif query_object.tab == 1:
            # 待我审核
            conditions.append(func.find_in_set(str(user_id), OaPurchase.check_uids))
        elif query_object.tab == 2:
            # 我已审核
            conditions.append(func.find_in_set(str(user_id), OaPurchase.check_history_uids))

        # 数据权限过滤（非管理员且非特定 tab）
        if query_object.tab == 0 and not is_admin:
            permission_conditions = [
                OaPurchase.admin_id == user_id,
                OaPurchase.prepared_uid == user_id,
                OaPurchase.sign_uid == user_id,
                OaPurchase.keeper_uid == user_id,
                func.find_in_set(str(user_id), OaPurchase.share_ids),
                func.find_in_set(str(user_id), OaPurchase.check_uids),
                func.find_in_set(str(user_id), OaPurchase.check_history_uids),
                ]

            # 部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    permission_conditions.append(OaPurchase.did.in_(dept_ids))

            if permission_conditions:
                conditions.append(or_(*permission_conditions))

        query = (
            select(OaPurchase)
            .where(*conditions)
            .order_by(OaPurchase.create_time.desc())
            .distinct()
        )

        purchase_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return purchase_list

    @classmethod
    async def add(cls, db: AsyncSession, model: dict[str, Any]):
        """
        新增采购合同

        :param db: orm 对象
        :param model: 采购合同模型字典
        :return:
        """
        db_model = OaPurchase(**model)
        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    @classmethod
    async def update(cls, db: AsyncSession, model: dict[str, Any]):
        """
        更新采购合同

        :param db: orm 对象
        :param model: 采购合同模型字典
        :return:
        """
        from sqlalchemy import update
        result = await db.execute(
            update(OaPurchase)
            .values(**model)
            .where(OaPurchase.id == model.get('id'))
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def delete(cls, db: AsyncSession, purchase_id: int, update_time: int):
        """
        删除采购合同（逻辑删除）

        :param db: orm 对象
        :param purchase_id: 采购合同 ID
        :param update_time: 更新时间
        :return:
        """
        from sqlalchemy import update
        result = await db.execute(
            update(OaPurchase)
            .values(delete_time=update_time, update_time=update_time)
            .where(OaPurchase.id == purchase_id)
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_by_id(cls, db: AsyncSession, purchase_id: int) -> OaPurchase | None:
        """
        根据 ID 获取采购合同详情

        :param db: orm 对象
        :param purchase_id: 采购合同 ID
        :return: 采购合同对象
        """
        query = select(OaPurchase).where(
            OaPurchase.id == purchase_id,
            OaPurchase.delete_time == 0
        )
        purchase_info = (await db.execute(query)).scalars().first()
        return purchase_info

    @classmethod
    async def get_by_name(cls, db: AsyncSession, model: dict[str, Any]) -> OaPurchase | None:
        """
        根据名称获取采购合同信息

        :param db: orm 对象
        :param model: 采购合同模型字典
        :return: 采购合同对象
        """
        query = select(OaPurchase).where(
            OaPurchase.name == model.get('name'),
            OaPurchase.delete_time == 0
        )
        purchase_info = (await db.execute(query)).scalars().first()
        return purchase_info

    @classmethod
    async def get_purchase_count(cls, db: AsyncSession, user_id:int):
        """
        获取用户合同统计信息

        :param user_id:
        :param db: orm 对象
        :param customer_id: 客户 ID
        :param exclude_id: 排除的合同 ID（编辑时使用）
        :return: True 表示已存在，False 表示不存在
        """
        query = select(func.count()).select_from(OaPurchase).where(OaPurchase.sign_uid == user_id, OaPurchase.delete_time == 0, OaPurchase.check_status == 2)
        result = await db.execute(query)
        count = result.scalar()
        return count

    @classmethod
    async def get_wait_check_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审采购合同数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审采购合同数量
        """
        query = select(func.count()).select_from(OaPurchase).where(
            OaPurchase.delete_time == 0,
            OaPurchase.check_status == 1,
            func.find_in_set(str(user_id), OaPurchase.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count


