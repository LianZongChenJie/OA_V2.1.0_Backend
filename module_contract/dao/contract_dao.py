# module_contract/dao/contract_dao.py
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_contract.entity.do.contract_do import OaContract
from module_contract.entity.vo.contract_vo import ContractModel, ContractPageQueryModel
from utils.log_util import logger
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
            from module_admin.dao.contract_cate_dao import ContractCateDao
            try:
                cate_info = await ContractCateDao.get_contract_cate_detail_by_id(db, contract_info.cate_id)
                if cate_info:
                    result['cate_title'] = cate_info.title
                else:
                    logger.warning(f'详情接口 - 未找到合同分类 ID: {contract_info.cate_id}')
            except Exception as e:
                logger.error(f'详情接口 - 查询合同分类名称失败: {e}, cate_id: {contract_info.cate_id}')

        # 查询签约主体名称
        if contract_info.subject_id:
            from module_basicdata.dao.public.enterprise_dao import EnterpriseDao
            try:
                subject_id_int = int(contract_info.subject_id)
                if subject_id_int > 0:
                    subject_info = await EnterpriseDao.get_enterprise_info(db, subject_id_int)
                    if subject_info:
                        result['subject_title'] = subject_info.title
            except (ValueError, TypeError):
                pass

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
        根据查询参数获取合同列表信息（优化版）

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 合同列表信息对象
        """
        from utils.timeformat import format_date

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

        if query_object.types is not None:
            conditions.append(OaContract.types == query_object.types)

        if query_object.cate_id is not None:
            conditions.append(OaContract.cate_id == query_object.cate_id)

        if query_object.check_status is not None:
            conditions.append(OaContract.check_status == query_object.check_status)

        if query_object.sign_time_start is not None:
            conditions.append(OaContract.sign_time >= query_object.sign_time_start)
        if query_object.sign_time_end is not None:
            conditions.append(OaContract.sign_time <= query_object.sign_time_end)

        if query_object.end_time_start is not None:
            conditions.append(OaContract.end_time >= query_object.end_time_start)
        if query_object.end_time_end is not None:
            conditions.append(OaContract.end_time <= query_object.end_time_end)

        if query_object.tab == 0:
            if query_object.sign_uid is not None:
                conditions.append(OaContract.sign_uid == query_object.sign_uid)
        elif query_object.tab == 1:
            conditions.append(func.find_in_set(str(user_id), OaContract.check_uids))
        elif query_object.tab == 2:
            conditions.append(func.find_in_set(str(user_id), OaContract.check_history_uids))

        # 不进行权限过滤，权限控制由菜单是否显示来处理
        # 只按查询参数（如 tab）进行过滤

        # 关联查询分类名称，避免 N+1 查询
        from module_admin.entity.do.contract_cate_do import OaContractCate
        query = (
            select(
                OaContract,
                OaContractCate.title.label('cate_name')
            )
            .outerjoin(OaContractCate, OaContract.cate_id == OaContractCate.id)
            .where(*conditions)
            .order_by(OaContract.create_time.desc())
        )

        contract_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        # 批量处理扩展字段，减少数据库查询
        if isinstance(contract_list, PageModel) and hasattr(contract_list, 'rows'):
            contract_list.rows = await cls._batch_process_contract_rows(db, contract_list.rows, format_date)
        elif isinstance(contract_list, list):
            contract_list = await cls._batch_process_contract_rows(db, contract_list, format_date)

        return contract_list

    @classmethod
    async def _batch_process_contract_rows(cls, db: AsyncSession, rows: list, format_date_func) -> list[dict[str, Any]]:
        """
        批量处理合同行数据，使用批量查询减少数据库交互

        :param db: orm 对象
        :param rows: 合同行数据列表
        :param format_date_func: 日期格式化函数
        :return: 处理后的字典数据列表
        """
        from utils.camel_converter import ModelConverter
        
        processed_rows = []
        
        # 收集需要查询的用户ID、部门ID和签约主体ID
        user_ids = set()
        dept_ids = set()
        subject_ids = set()
        
        for row in rows:
            if isinstance(row, (list, tuple)):
                contract_obj = row[0]
            else:
                contract_obj = row
            
            if hasattr(contract_obj, '__table__'):
                row_dict = ModelConverter.to_dict(contract_obj, by_alias=True)
            elif isinstance(contract_obj, dict):
                row_dict = contract_obj
            else:
                continue
            
            # 收集用户ID（包含归档人、作废人、终止人）- 优先检查驼峰格式（PageUtil.paginate 返回驼峰格式）
            for field in ['adminId', 'preparedUid', 'signUid', 'keeperUid', 'archiveUid', 'voidUid', 'stopUid']:
                val = row_dict.get(field)
                if val and int(val) > 0:
                    user_ids.add(int(val))
            
            # 收集部门ID
            did = row_dict.get('did')
            if did and int(did) > 0:
                dept_ids.add(int(did))
            
            # 收集签约主体ID - 优先检查驼峰格式（PageUtil.paginate 返回驼峰格式）
            subject_id = row_dict.get('subjectId') or row_dict.get('subject_id')
            if subject_id:
                try:
                    subject_id_int = int(subject_id)
                    if subject_id_int > 0:
                        subject_ids.add(subject_id_int)
                except (ValueError, TypeError):
                    pass
            
            processed_rows.append(row_dict)
        
        # 批量查询用户信息
        user_map = await cls._batch_get_users(db, user_ids)
        
        # 批量查询部门信息
        dept_map = await cls._batch_get_depts(db, dept_ids)
        
        # 批量查询签约主体信息
        subject_map = await cls._batch_get_subjects(db, subject_ids)
        
        # 填充扩展字段
        for i, row in enumerate(processed_rows):
            # 获取分类名称（从 JOIN 查询结果）
            if isinstance(rows[i], (list, tuple)) and len(rows[i]) > 1:
                row['cateName'] = rows[i][1] or None
            else:
                row['cateName'] = None
            
            # 填充用户名称
            admin_id = row.get('adminId')
            row['adminName'] = user_map.get(int(admin_id)) if admin_id else None
            
            prepared_uid = row.get('preparedUid')
            row['preparedName'] = user_map.get(int(prepared_uid)) if prepared_uid else None
            
            sign_uid = row.get('signUid')
            row['signName'] = user_map.get(int(sign_uid)) if sign_uid else None
            
            keeper_uid = row.get('keeperUid')
            row['keeperName'] = user_map.get(int(keeper_uid)) if keeper_uid else None
            
            # 填充归档人名称
            archive_uid = row.get('archiveUid')
            row['archiveUidName'] = user_map.get(int(archive_uid)) if archive_uid else None
            
            # 填作废人名称
            void_uid = row.get('voidUid')
            row['voidUidName'] = user_map.get(int(void_uid)) if void_uid else None
            
            # 填充终止人名称
            stop_uid = row.get('stopUid')
            row['stopUidName'] = user_map.get(int(stop_uid)) if stop_uid else None
            
            # 填充部门名称
            did = row.get('did')
            row['deptName'] = dept_map.get(int(did)) if did else None
            
            # 填充签约主体名称
            subject_id = row.get('subjectId')
            if subject_id:
                try:
                    row['subjectName'] = subject_map.get(int(subject_id))
                except (ValueError, TypeError):
                    row['subjectName'] = None
            else:
                row['subjectName'] = None
            
            # 格式化时间字段
            for time_field in ['startTime', 'endTime', 'signTime']:
                val = row.get(time_field)
                if val and int(val) > 0:
                    row[f'{time_field}Str'] = format_date_func(int(val), '%Y-%m-%d')
                else:
                    row[f'{time_field}Str'] = None
            
            for time_field in ['createTime', 'updateTime', 'stopTime', 'voidTime', 'archiveTime', 'checkTime']:
                val = row.get(time_field)
                if val and int(val) > 0:
                    row[f'{time_field}Str'] = format_date_func(int(val), '%Y-%m-%d %H:%M:%S')
                else:
                    row[f'{time_field}Str'] = None
        
        return processed_rows

    @classmethod
    async def _batch_get_users(cls, db: AsyncSession, user_ids: set) -> dict:
        """
        批量获取用户名称（不限制用户状态，用于显示历史操作人）

        :param db: orm 对象
        :param user_ids: 用户ID集合
        :return: 用户ID到名称的映射
        """
        if not user_ids:
            return {}
        
        from module_admin.entity.do.user_do import SysUser
        from sqlalchemy import select
        
        user_map = {}
        
        for user_id in user_ids:
            try:
                # 直接查询用户，不限制状态（用于显示归档人等历史操作人）
                user_info = (
                    (await db.execute(select(SysUser).where(SysUser.user_id == user_id)))
                    .scalars()
                    .first()
                )
                if user_info:
                    user_map[user_id] = user_info.nick_name or user_info.user_name
            except Exception as e:
                logger.error(f'批量查询用户失败: user_id={user_id}, error={e}')
        
        return user_map

    @classmethod
    async def _batch_get_depts(cls, db: AsyncSession, dept_ids: set) -> dict:
        """
        批量获取部门名称

        :param db: orm 对象
        :param dept_ids: 部门ID集合
        :return: 部门ID到名称的映射
        """
        if not dept_ids:
            return {}
        
        from module_admin.dao.dept_dao import DeptDao
        dept_map = {}
        
        for dept_id in dept_ids:
            try:
                dept_info = await DeptDao.get_dept_detail_by_id(db, dept_id)
                if dept_info:
                    dept_map[dept_id] = dept_info.dept_name
            except Exception as e:
                logger.error(f'批量查询部门失败: dept_id={dept_id}, error={e}')
        
        return dept_map

    @classmethod
    async def _batch_get_subjects(cls, db: AsyncSession, subject_ids: set) -> dict:
        """
        批量获取签约主体名称

        :param db: orm 对象
        :param subject_ids: 签约主体ID集合
        :return: 签约主体ID到名称的映射
        """
        if not subject_ids:
            return {}
        
        from module_basicdata.dao.public.enterprise_dao import EnterpriseDao
        subject_map = {}
        
        for subject_id in subject_ids:
            try:
                subject_info = await EnterpriseDao.get_enterprise_info(db, subject_id)
                if subject_info:
                    subject_map[subject_id] = subject_info.title
            except Exception as e:
                logger.error(f'批量查询签约主体失败: subject_id={subject_id}, error={e}')
        
        return subject_map

    @classmethod
    async def _process_contract_row(cls, db: AsyncSession, row: Any, format_date_func) -> dict[str, Any]:
        """
        处理合同行数据，添加扩展字段

        :param db: orm 对象
        :param row: 合同行数据（已经是字典格式，由 PageUtil.paginate 转换）
        :param format_date_func: 日期格式化函数
        :return: 处理后的字典数据
        """
        # PageUtil.paginate 已经将其转换为字典并做了驼峰转换
        # 所以这里 row 是字典，且键名是驼峰格式
        if not isinstance(row, dict):
            # 如果不是字典，说明 PageUtil 没有转换，需要手动处理
            if hasattr(row, '__table__'):
                # ORM 对象，转换为字典
                from utils.camel_converter import ModelConverter
                row = ModelConverter.to_dict(row, by_alias=True)
            else:
                # 其他类型，直接返回
                return row

        # 从字典中获取数据（驼峰命名）
        row_id = row.get('id')
        cate_id = row.get('cateId')
        subject_id = row.get('subjectId')
        prepared_uid = row.get('preparedUid')
        admin_id = row.get('adminId')
        did = row.get('did')
        sign_uid = row.get('signUid')
        keeper_uid = row.get('keeperUid')
        start_time = row.get('startTime')
        end_time = row.get('endTime')
        sign_time = row.get('signTime')
        create_time = row.get('createTime')
        update_time = row.get('updateTime')
        stop_time = row.get('stopTime')
        void_time = row.get('voidTime')
        archive_time = row.get('archiveTime')
        check_time = row.get('checkTime')
        
        # 构建结果字典，保留所有原始字段
        result = row.copy()

        # 初始化扩展字段
        result['cateName'] = None
        result['subjectName'] = None
        result['adminName'] = None
        result['preparedName'] = None
        result['deptName'] = None
        result['signName'] = None
        result['keeperName'] = None
        result['startTimeStr'] = None
        result['endTimeStr'] = None
        result['signTimeStr'] = None
        result['createTimeStr'] = None
        result['updateTimeStr'] = None
        result['stopTimeStr'] = None
        result['voidTimeStr'] = None
        result['archiveTimeStr'] = None
        result['checkTimeStr'] = None

        # 查询分类名称
        if cate_id and int(cate_id) > 0:
            from module_admin.dao.contract_cate_dao import ContractCateDao
            try:
                cate_info = await ContractCateDao.get_contract_cate_detail_by_id(db, int(cate_id))
                if cate_info:
                    result['cateName'] = cate_info.title
                else:
                    logger.warning(f'列表接口 - 未找到合同分类 ID: {cate_id}')
            except Exception as e:
                logger.error(f'列表接口 - 查询合同分类名称失败: {e}, cate_id: {cate_id}')

        # 查询签约主体名称
        if subject_id:
            from module_basicdata.dao.public.enterprise_dao import EnterpriseDao
            try:
                subject_id_int = int(subject_id)
                if subject_id_int > 0:
                    subject_info = await EnterpriseDao.get_enterprise_info(db, subject_id_int)
                    if subject_info:
                        result['subjectName'] = subject_info.title
            except (ValueError, TypeError):
                pass

        # 查询创建人姓名
        if admin_id and int(admin_id) > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(db, int(admin_id))
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                result['adminName'] = admin_info.nick_name or admin_info.user_name

        # 查询合同制定人姓名
        if prepared_uid and int(prepared_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            prepared_result = await UserDao.get_user_by_id(db, int(prepared_uid))
            if prepared_result and prepared_result.get('user_basic_info'):
                prepared_info = prepared_result['user_basic_info']
                result['preparedName'] = prepared_info.nick_name or prepared_info.user_name

        # 查询所属部门名称
        if did and int(did) > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_detail_by_id(db, int(did))
            if dept_info:
                result['deptName'] = dept_info.dept_name

        # 查询签订人姓名
        if sign_uid and int(sign_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            sign_result = await UserDao.get_user_by_id(db, int(sign_uid))
            if sign_result and sign_result.get('user_basic_info'):
                sign_info = sign_result['user_basic_info']
                result['signName'] = sign_info.nick_name or sign_info.user_name

        # 查询保管人姓名
        if keeper_uid and int(keeper_uid) > 0:
            from module_admin.dao.user_dao import UserDao
            keeper_result = await UserDao.get_user_by_id(db, int(keeper_uid))
            if keeper_result and keeper_result.get('user_basic_info'):
                keeper_info = keeper_result['user_basic_info']
                result['keeperName'] = keeper_info.nick_name or keeper_info.user_name

        # 格式化合同开始时间
        if start_time and int(start_time) > 0:
            result['startTimeStr'] = format_date_func(int(start_time), '%Y-%m-%d')

        # 格式化合同结束时间
        if end_time and int(end_time) > 0:
            result['endTimeStr'] = format_date_func(int(end_time), '%Y-%m-%d')

        # 格式化签订日期
        if sign_time and int(sign_time) > 0:
            result['signTimeStr'] = format_date_func(int(sign_time), '%Y-%m-%d')

        # 格式化创建时间
        if create_time and int(create_time) > 0:
            result['createTimeStr'] = format_date_func(int(create_time), '%Y-%m-%d %H:%M:%S')

        # 格式化更新时间
        if update_time and int(update_time) > 0:
            result['updateTimeStr'] = format_date_func(int(update_time), '%Y-%m-%d %H:%M:%S')

        # 格式化中止时间
        if stop_time and int(stop_time) > 0:
            result['stopTimeStr'] = format_date_func(int(stop_time), '%Y-%m-%d %H:%M:%S')

        # 格式化作废时间
        if void_time and int(void_time) > 0:
            result['voidTimeStr'] = format_date_func(int(void_time), '%Y-%m-%d %H:%M:%S')

        # 格式化归档时间
        if archive_time and int(archive_time) > 0:
            result['archiveTimeStr'] = format_date_func(int(archive_time), '%Y-%m-%d %H:%M:%S')

        # 格式化审核通过时间
        if check_time and int(check_time) > 0:
            result['checkTimeStr'] = format_date_func(int(check_time), '%Y-%m-%d %H:%M:%S')

        return result

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


    @classmethod
    async def get_contract_count(cls, db: AsyncSession, user_id:int):
        """
        获取用户销售合同统计信息

        :param user_id: 用户ID
        :param db: orm 对象
        :return: 合同数量
        """
        from sqlalchemy import or_
        
        query = select(func.count()).select_from(OaContract).where(
            OaContract.delete_time == 0, 
            OaContract.check_status != 3,  # 排除审核不通过的
            or_(
                OaContract.admin_id == user_id,  # 我创建的
                OaContract.sign_uid == user_id,  # 我是签订人的
                func.find_in_set(str(user_id), OaContract.share_ids)  # 共享给我的
            )
        )
        result = await db.execute(query)
        count = result.scalar()
        return count

    @classmethod
    async def get_wait_check_count(cls, db: AsyncSession, user_id: int):
        """
        获取待审销售合同数量

        :param db: orm 对象
        :param user_id: 用户 ID
        :return: 待审公销售合同数量
        """
        query = select(func.count()).select_from(OaContract).where(
            OaContract.delete_time == 0,
            OaContract.check_status == 1,
            func.find_in_set(str(user_id), OaContract.check_uids),
        )
        result = await db.execute(query)
        count = result.scalar()
        return count

    @classmethod
    async def get_by_name(cls, db: AsyncSession, contract_data: dict) -> OaContract | None:
        """
        根据名称获取合同（用于验重）

        :param db: orm 对象
        :param contract_data: 合同数据
        :return: 合同对象
        """
        query = select(OaContract).where(
            OaContract.name == contract_data.get('name'),
            OaContract.delete_time == 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def archive_contract(cls, db: AsyncSession, contract_id: int, archive_uid: int, archive_time: int) -> int:
        """
        归档销售合同

        :param db: orm 对象
        :param contract_id: 销售合同 ID
        :param archive_uid: 归档人 ID
        :param archive_time: 归档时间
        :return: 影响行数
        """
        result = await db.execute(
            update(OaContract)
            .values(
                archive_uid=archive_uid,
                archive_time=archive_time,
                update_time=archive_time
            )
            .where(OaContract.id == contract_id)
        )
        await db.commit()
        return result.rowcount