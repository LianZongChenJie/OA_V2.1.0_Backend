# module_contract/dao/contract_dao.py
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_contract.entity.do.contract_do import OaContract
from module_contract.entity.vo.contract_vo import ContractModel, ContractPageQueryModel
from utils.page_util import PageUtil


class ContractDao:
    """
    销售合同管理模块数据库操作层
    """

    @classmethod
    async def get_contract_detail_by_id(cls, db: AsyncSession, contract_id: int) -> dict[str, Any] | None:
        """
        根据合同 ID 获取合同详细信息

        :param db: orm 对象
        :param contract_id: 合同 ID
        :return: 合同详细信息对象
        """
        query = select(OaContract).where(OaContract.id == contract_id, OaContract.delete_time == 0)
        contract_info = (await db.execute(query)).scalars().first()

        if not contract_info:
            return None

        result = {
            'contract_info': contract_info,
            'cate_title': None,
            'subject_title': None,
            'admin_name': None,
            'prepared_name': None,
            'sign_name': None,
            'keeper_name': None,
            'share_names': [],
            'check_status_name': None,
        }

        # 查询分类名称
        if contract_info.cate_id and contract_info.cate_id > 0:
            from module_basicdata.dao.project.project_cate_dao import ProjectCateDao
            cate_info = await ProjectCateDao.get_info_by_id(db, contract_info.cate_id)
            if cate_info:
                result['cate_title'] = cate_info.title

        # 查询创建人姓名
        if contract_info.admin_id and contract_info.admin_id > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, contract_info.admin_id)
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                result['admin_name'] = admin_info.nick_name or admin_info.user_name

        # 查询合同制定人姓名
        if contract_info.prepared_uid and contract_info.prepared_uid > 0:
            from module_admin.dao.user_dao import UserDao
            prepared_result = await UserDao.get_user_by_id(db, contract_info.prepared_uid)
            if prepared_result and prepared_result.get('user_basic_info'):
                prepared_info = prepared_result['user_basic_info']
                result['prepared_name'] = prepared_info.nick_name or prepared_info.user_name

        # 查询合同签订人姓名
        if contract_info.sign_uid and contract_info.sign_uid > 0:
            from module_admin.dao.user_dao import UserDao
            sign_result = await UserDao.get_user_by_id(db, contract_info.sign_uid)
            if sign_result and sign_result.get('user_basic_info'):
                sign_info = sign_result['user_basic_info']
                result['sign_name'] = sign_info.nick_name or sign_info.user_name

        # 查询合同保管人姓名
        if contract_info.keeper_uid and contract_info.keeper_uid > 0:
            from module_admin.dao.user_dao import UserDao
            keeper_result = await UserDao.get_user_by_id(db, contract_info.keeper_uid)
            if keeper_result and keeper_result.get('user_basic_info'):
                keeper_info = keeper_result['user_basic_info']
                result['keeper_name'] = keeper_info.nick_name or keeper_info.user_name

        # 查询共享人员姓名列表（简化处理，不查询）
        # 如果需要查询，可以遍历 share_ids 逐个查询

        # 设置审核状态名称
        check_status_map = {
            0: '待审核',
            1: '审核中',
            2: '审核通过',
            3: '审核不通过',
            4: '撤销审核'
        }
        if contract_info.check_status is not None:
            result['check_status_name'] = check_status_map.get(contract_info.check_status, '未知')

        return result

    @classmethod
    async def get_contract_detail_by_info(cls, db: AsyncSession, contract: ContractModel) -> OaContract | None:
        """
        根据合同参数获取信息

        :param db: orm 对象
        :param contract: 合同参数对象
        :return: 合同信息对象
        """
        query_conditions = [OaContract.delete_time == 0]

        if contract.id is not None:
            query_conditions.append(OaContract.id == contract.id)
        if contract.name:
            query_conditions.append(OaContract.name == contract.name)

        if query_conditions:
            contract_info = (
                (await db.execute(select(OaContract).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            contract_info = None

        return contract_info

    @classmethod
    async def get_contract_list(
            cls, db: AsyncSession, query_object: ContractPageQueryModel, user_id: int,
            auth_dids: str = '', son_dids: str = '', is_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取合同列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 合同列表信息对象
        """
        # 基础条件：未删除
        conditions = [OaContract.delete_time == 0]

        # 根据状态标志设置不同的查询条件
        if hasattr(query_object, 'archive_status') and query_object.archive_status == 1:
            # 已归档合同
            conditions.append(OaContract.archive_time > 0)
        elif hasattr(query_object, 'stop_status') and query_object.stop_status == 1:
            # 已中止合同
            conditions.append(OaContract.stop_time > 0)
        elif hasattr(query_object, 'void_status') and query_object.void_status == 1:
            # 已作废合同
            conditions.append(OaContract.void_time > 0)
        else:
            # 正常合同：未归档、未中止、未作废
            conditions.append(OaContract.archive_time == 0)
            conditions.append(OaContract.stop_time == 0)
            conditions.append(OaContract.void_time == 0)

        # 关键词搜索
        if query_object.keywords:
            conditions.append(
                or_(
                    OaContract.id.like(f'%{query_object.keywords}%'),
                    OaContract.name.like(f'%{query_object.keywords}%'),
                    OaContract.code.like(f'%{query_object.keywords}%')
                )
            )

        # 合同性质筛选
        if query_object.types_filter is not None:
            conditions.append(OaContract.types == query_object.types_filter)

        # 分类筛选
        if query_object.cate_id_filter is not None:
            conditions.append(OaContract.cate_id == query_object.cate_id_filter)

        # 审核状态筛选
        if query_object.check_status_filter is not None:
            conditions.append(OaContract.check_status == query_object.check_status_filter)

        # 签订时间范围
        if query_object.sign_time_start is not None:
            conditions.append(OaContract.sign_time >= query_object.sign_time_start)
        if query_object.sign_time_end is not None:
            conditions.append(OaContract.sign_time <= query_object.sign_time_end)

        # 结束时间范围
        if query_object.end_time_start is not None:
            conditions.append(OaContract.end_time >= query_object.end_time_start)
        if query_object.end_time_end is not None:
            conditions.append(OaContract.end_time <= query_object.end_time_end)

        # 根据 tab 参数设置查询条件
        if query_object.tab == 0:
            # 全部合同（根据权限过滤）
            if query_object.admin_id_filter is not None:
                conditions.append(OaContract.sign_uid == query_object.admin_id_filter)
        elif query_object.tab == 1:
            # 待我审核
            conditions.append(func.find_in_set(str(user_id), OaContract.check_uids))
        elif query_object.tab == 2:
            # 我已审核
            conditions.append(func.find_in_set(str(user_id), OaContract.check_history_uids))

        # 数据权限过滤（非管理员且非特定 tab）
        if query_object.tab == 0 and not is_admin:
            permission_conditions = [
                OaContract.admin_id == user_id,
                OaContract.prepared_uid == user_id,
                OaContract.sign_uid == user_id,
                OaContract.keeper_uid == user_id,
                func.find_in_set(str(user_id), OaContract.share_ids),
                func.find_in_set(str(user_id), OaContract.check_uids),
                func.find_in_set(str(user_id), OaContract.check_history_uids),
                ]

            # 部门权限
            if auth_dids or son_dids:
                dept_ids = set()
                if auth_dids:
                    dept_ids.update([int(d.strip()) for d in auth_dids.split(',') if d.strip()])
                if son_dids:
                    dept_ids.update([int(d.strip()) for d in son_dids.split(',') if d.strip()])

                if dept_ids:
                    permission_conditions.append(OaContract.did.in_(dept_ids))

            if permission_conditions:
                conditions.append(or_(*permission_conditions))

        query = (
            select(OaContract)
            .where(*conditions)
            .order_by(OaContract.create_time.desc())
            .distinct()
        )

        contract_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return contract_list



    @classmethod
    async def add_contract_dao(cls, db: AsyncSession, contract: dict | ContractModel) -> OaContract:
        """
        新增合同数据库操作

        :param db: orm 对象
        :param contract: 合同对象或字典
        :return:
        """
        from pydantic import BaseModel
        
        # 如果是 Pydantic 模型，转换为字典
        if isinstance(contract, BaseModel):
            contract_data = contract.model_dump()
        else:
            contract_data = contract
            
        # 只提取 OaContract 模型中存在的字段，排除扩展字段
        valid_fields = {c.name for c in OaContract.__table__.columns}
        filtered_data = {
            k: v for k, v in contract_data.items() 
            if k in valid_fields
        }
        db_contract = OaContract(**filtered_data)
        db.add(db_contract)
        await db.flush()

        return db_contract

    @classmethod
    async def edit_contract_dao(cls, db: AsyncSession, contract_id: int, contract: dict) -> None:
        """
        编辑合同数据库操作

        :param db: orm 对象
        :param contract_id: 合同 ID
        :param contract: 需要更新的合同字典
        :return:
        """
        await db.execute(
            update(OaContract)
            .where(OaContract.id == contract_id)
            .values(**contract)
        )

    @classmethod
    async def delete_contract_dao(cls, db: AsyncSession, contract: ContractModel) -> None:
        """
        删除合同数据库操作（逻辑删除）

        :param db: orm 对象
        :param contract: 合同对象
        :return:
        """
        update_time = contract.update_time if contract.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaContract)
            .where(OaContract.id == contract.id)
            .values(delete_time=update_time, update_time=update_time)
        )

    @classmethod
    async def check_chance_exists(cls, db: AsyncSession, chance_id: int, exclude_id: int | None = None) -> bool:
        """
        检查销售机会是否已关联合同

        :param db: orm 对象
        :param chance_id: 销售机会 ID
        :param exclude_id: 排除的合同 ID（编辑时使用）
        :return: True 表示已存在，False 表示不存在
        """
        query = select(OaContract.id).where(
            OaContract.chance_id == chance_id,
            OaContract.delete_time == 0
        )

        if exclude_id is not None:
            query = query.where(OaContract.id != exclude_id)

        result = await db.execute(query)
        return result.scalar() is not None

