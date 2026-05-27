from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_contract.dao.purchase_dao import PurchaseDao
from module_contract.entity.do.purchase_do import OaPurchase
from module_contract.entity.vo.purchase_vo import (
    AddPurchaseModel,
    DeletePurchaseModel,
    EditPurchaseModel,
    PurchaseModel,
    PurchasePageQueryModel,
)
from utils.log_util import logger


class PurchaseService:
    """
    采购合同管理模块业务逻辑层
    """

    @classmethod
    async def check_purchase_name_unique_services(cls, query_db: AsyncSession, page_object: AddPurchaseModel | EditPurchaseModel) -> bool:
        """
        校验采购合同名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 采购合同对象
        :return: 校验结果（True=唯一，False=不唯一）
        """
        # 如果是编辑操作，排除自身
        purchase_id = -1 if page_object.id is None else page_object.id
        existing_purchase = await PurchaseDao.get_by_name(query_db, page_object.model_dump())
        
        if existing_purchase and existing_purchase.id != purchase_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def get_purchase_list_services(
            cls, query_db: AsyncSession, query_object: PurchasePageQueryModel,
            current_user_id: int, auth_dids: str = '', son_dids: str = '',
            is_admin: bool = False, is_contract_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取采购合同列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_contract_admin: 是否为采购合同管理员
        :param is_page: 是否开启分页
        :return: 采购合同列表信息对象
        """
        # 如果是采购合同管理员，不进行权限过滤
        if is_contract_admin:
            purchase_list_result = await PurchaseDao.get_purchase_list(
                query_db, query_object, current_user_id, '', '', True, is_page
            )
        else:
            purchase_list_result = await PurchaseDao.get_purchase_list(
                query_db, query_object, current_user_id, auth_dids, son_dids, is_admin, is_page
            )

        return purchase_list_result

    @classmethod
    async def add_purchase_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPurchaseModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增采购合同信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 采购合同对象
        :param current_user_id: 当前用户 ID
        :return: 新增结果
        """
        try:
            # 验重：检查合同名称是否已存在
            if not await cls.check_purchase_name_unique_services(query_db, page_object):
                raise ServiceException(message='合同名称已存在')

            # 设置创建时间和更新时间
            current_time = int(datetime.now().timestamp())
            
            # 从原始请求体中获取所有字段（包括 Pydantic 未识别的字段）
            try:
                raw_body = await request.json()
            except Exception:
                raw_body = {}
            
            # 获取模型数据（不使用 by_alias，保持下划线格式）
            purchase_data = page_object.model_dump(exclude={"id", "create_time", "update_time"}, exclude_none=True)
            
            # 合并原始请求体中的字段（优先使用原始请求体中的值）
            for key, value in raw_body.items():
                if key not in purchase_data:
                    purchase_data[key] = value
            
            # 字段映射：前端驼峰字段 -> 数据库字段
            field_mapping = {
                'customerId': 'supplier_id',
                'customer': 'supplier',
                'cateId': 'cate_id',
                'subjectId': 'subject_id',
                'contactName': 'contact_name',
                'contactMobile': 'contact_mobile',
                'contactAddress': 'contact_address',
                'preparedUid': 'prepared_uid',
                'signUid': 'sign_uid',
                'keeperUid': 'keeper_uid',
                'shareIds': 'share_ids',
                'checkStatus': 'check_status',
                'signTime': 'sign_time',
                'startTime': 'start_time',
                'endTime': 'end_time',
            }
            
            # 处理映射字段
            for front_field, db_field in field_mapping.items():
                if front_field in purchase_data:
                    value = purchase_data.pop(front_field)
                    # 处理时间字段：将字符串日期转换为时间戳，强制格式化为 yyyy-mm-dd
                    if db_field in ['sign_time', 'start_time', 'end_time'] and isinstance(value, str):
                        try:
                            # 尝试解析包含时分秒的格式
                            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                            # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                            value = int(dt.timestamp())
                        except ValueError:
                            try:
                                # 尝试解析仅日期格式
                                dt = datetime.strptime(value, '%Y-%m-%d')
                                value = int(dt.timestamp())
                            except (ValueError, TypeError):
                                value = 0
                    purchase_data[db_field] = value
            
            # 处理 contractTime 字段（前端传入的时间范围数组）
            if 'contractTime' in purchase_data:
                contract_time = purchase_data.pop('contractTime')
                if isinstance(contract_time, list) and len(contract_time) >= 2:
                    try:
                        # 尝试解析包含时分秒的格式
                        start_dt = datetime.strptime(contract_time[0], '%Y-%m-%d %H:%M:%S')
                        # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                        purchase_data['start_time'] = int(start_dt.timestamp())
                    except ValueError:
                        try:
                            # 尝试解析仅日期格式
                            start_dt = datetime.strptime(contract_time[0], '%Y-%m-%d')
                            purchase_data['start_time'] = int(start_dt.timestamp())
                        except (ValueError, TypeError):
                            pass
                    try:
                        # 尝试解析包含时分秒的格式
                        end_dt = datetime.strptime(contract_time[1], '%Y-%m-%d %H:%M:%S')
                        # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                        end_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                        purchase_data['end_time'] = int(end_dt.timestamp())
                    except ValueError:
                        try:
                            # 尝试解析仅日期格式
                            end_dt = datetime.strptime(contract_time[1], '%Y-%m-%d')
                            purchase_data['end_time'] = int(end_dt.timestamp())
                        except (ValueError, TypeError):
                            pass
            
            # 移除不需要传递给数据库的字段
            extra_fields = ['contractTime', 'deptName', 'signUserName', 'preparedUserName', 'keeperUserName']
            for field in extra_fields:
                purchase_data.pop(field, None)
            
            purchase_data['admin_id'] = current_user_id
            purchase_data['create_time'] = current_time
            purchase_data['update_time'] = current_time
            
            await PurchaseDao.add(query_db, purchase_data)
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_purchase_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPurchaseModel
    ) -> CrudResponseModel:
        """
        编辑采购合同信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 采购合同对象
        :return: 编辑结果
        """
        if page_object.id:
            try:
                existing_purchase = await PurchaseDao.get_by_id(query_db, page_object.id)
                if not existing_purchase:
                    raise ServiceException(message='采购合同不存在')

                if not await cls.check_purchase_name_unique_services(query_db, page_object):
                    raise ServiceException(message='合同名称已存在')

                current_time = int(datetime.now().timestamp())
                
                # 从原始请求体中获取所有字段（包括 Pydantic 未识别的字段）
                try:
                    raw_body = await request.json()
                except Exception:
                    raw_body = {}
                
                # 获取模型数据（包含前端传入的字段，使用 by_alias=True 获取驼峰格式）
                model_data = page_object.model_dump(exclude_unset=True, by_alias=True)
                
                # 合并原始请求体中的字段（优先使用原始请求体中的值）
                for key, value in raw_body.items():
                    if key not in model_data:
                        model_data[key] = value
                
                logger.info(f'采购合同编辑 - ID: {page_object.id}')
                logger.info(f'采购合同编辑 - 原始数据（驼峰）: {model_data}')
                
                # 字段映射：前端驼峰字段 -> 数据库字段
                field_mapping = {
                    'customerId': 'supplier_id',
                    'customer': 'supplier',
                    'cateId': 'cate_id',
                    'subjectId': 'subject_id',
                    'contactName': 'contact_name',
                    'contactMobile': 'contact_mobile',
                    'contactAddress': 'contact_address',
                    'preparedUid': 'prepared_uid',
                    'signUid': 'sign_uid',
                    'keeperUid': 'keeper_uid',
                    'shareIds': 'share_ids',
                    'checkStatus': 'check_status',
                }
                
                # 处理映射字段
                for front_field, db_field in field_mapping.items():
                    if front_field in model_data:
                        value = model_data.pop(front_field)
                        model_data[db_field] = value
                        logger.info(f'字段映射: {front_field}={value} -> {db_field}')
                
                # 处理 contractTime 字段（前端传入的时间范围数组，驼峰格式）
                # 支持字符串格式（如 '2026-04-16 00:00:00'）和整数格式（时间戳）
                # 强制格式化为 yyyy-mm-dd
                if 'contractTime' in model_data and isinstance(model_data['contractTime'], list) and len(model_data['contractTime']) >= 2:
                    try:
                        start_value = model_data['contractTime'][0]
                        end_value = model_data['contractTime'][1]
                        
                        if isinstance(start_value, str):
                            try:
                                # 尝试解析包含时分秒的格式
                                start_dt = datetime.strptime(start_value, '%Y-%m-%d %H:%M:%S')
                                # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                                model_data['start_time'] = int(start_dt.timestamp())
                            except ValueError:
                                # 尝试解析仅日期格式
                                start_dt = datetime.strptime(start_value, '%Y-%m-%d')
                                model_data['start_time'] = int(start_dt.timestamp())
                        elif isinstance(start_value, int):
                            model_data['start_time'] = start_value
                        
                        if isinstance(end_value, str):
                            try:
                                # 尝试解析包含时分秒的格式
                                end_dt = datetime.strptime(end_value, '%Y-%m-%d %H:%M:%S')
                                # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                                end_dt = end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                                model_data['end_time'] = int(end_dt.timestamp())
                            except ValueError:
                                # 尝试解析仅日期格式
                                end_dt = datetime.strptime(end_value, '%Y-%m-%d')
                                model_data['end_time'] = int(end_dt.timestamp())
                        elif isinstance(end_value, int):
                            model_data['end_time'] = end_value
                    except ValueError:
                        pass
                    del model_data['contractTime']
                
                # 处理时间字段转换为时间戳（驼峰格式）
                # 支持字符串格式（如 '2026-04-16 00:00:00'）和整数格式（时间戳）
                # 强制格式化为 yyyy-mm-dd
                camel_time_fields = {'startTime': 'start_time', 'endTime': 'end_time', 'signTime': 'sign_time'}
                for camel_field, db_field in camel_time_fields.items():
                    if camel_field in model_data:
                        value = model_data[camel_field]
                        if isinstance(value, str):
                            try:
                                # 尝试解析包含时分秒的格式
                                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                                # 强制格式化为 yyyy-mm-dd（取日期部分，时间设为00:00:00）
                                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                                model_data[db_field] = int(dt.timestamp())
                            except ValueError:
                                try:
                                    # 尝试解析仅日期格式
                                    dt = datetime.strptime(value, '%Y-%m-%d')
                                    model_data[db_field] = int(dt.timestamp())
                                except ValueError:
                                    pass
                        elif isinstance(value, int):
                            # 如果是整数，直接作为时间戳使用
                            model_data[db_field] = value
                        else:
                            model_data[db_field] = value
                        del model_data[camel_field]
                
                valid_fields = {c.name for c in OaPurchase.__table__.columns}
                exclude_fields = {'id', 'create_time', 'delete_time', 'admin_id'}
                
                purchase_data = {
                    k: v for k, v in model_data.items()
                    if k in valid_fields and k not in exclude_fields
                }
                
                logger.info(f'采购合同编辑 - 有效字段列表: {valid_fields}')
                logger.info(f'采购合同编辑 - 过滤后数据: {purchase_data}')
                logger.info(f'采购合同编辑 - supplier_id 是否在数据中: {"supplier_id" in purchase_data}')
                logger.info(f'采购合同编辑 - supplier 是否在数据中: {"supplier" in purchase_data}')
                
                if not purchase_data:
                    raise ServiceException(message='没有可更新的字段')
                
                purchase_data['update_time'] = current_time
                purchase_data['id'] = page_object.id
                
                result = await PurchaseDao.update(query_db, purchase_data)
                await query_db.commit()
                
                logger.info(f'采购合同编辑 - 更新结果: {result}, 已提交事务')
                
                return CrudResponseModel(is_success=True, message='修改成功')
            except Exception as e:
                await query_db.rollback()
                logger.error(f'采购合同编辑失败: {str(e)}', exc_info=True)
                raise e
        else:
            raise ServiceException(message='传入采购合同 id 为空')

    @classmethod
    async def delete_purchase_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePurchaseModel
    ) -> CrudResponseModel:
        """
        删除采购合同信息 service（逻辑删除）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 采购合同对象
        :return: 删除结果
        """
        if page_object.id:
            try:
                # 检查采购合同是否存在
                existing_purchase = await PurchaseDao.get_by_id(query_db, page_object.id)
                if not existing_purchase:
                    raise ServiceException(message='采购合同不存在')

                # 设置更新时间
                current_time = int(datetime.now().timestamp())
                
                await PurchaseDao.delete(query_db, page_object.id, current_time)
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入采购合同 id 为空')

    @classmethod
    async def purchase_detail_services(cls, query_db: AsyncSession, purchase_id: int) -> dict:
        """
        获取采购合同详细信息 service（使用 ORM 查询，与销售合同保持一致）

        :param query_db: orm 对象
        :param purchase_id: 采购合同 ID
        :return: 采购合同详细信息字典
        """
        from module_personnel.dao.flow_record_dao import FlowRecordDao
        from utils.time_format_util import timestamp_to_datetime
        
        # 使用 ORM 查询获取采购合同信息
        from module_contract.dao.purchase_dao import PurchaseDao
        from module_contract.entity.do.purchase_do import OaPurchase
        from sqlalchemy import select
        
        query = select(OaPurchase).where(
            OaPurchase.id == purchase_id,
            OaPurchase.delete_time == 0
        )
        result = await query_db.execute(query)
        purchase_info = result.scalar_one_or_none()
        
        if not purchase_info:
            return {}
        
        # 构建返回数据
        purchase_data = {}
        
        # 只提取数据库表存在的字段
        valid_fields = {c.name for c in OaPurchase.__table__.columns}
        for k in valid_fields:
            if hasattr(purchase_info, k):
                value = getattr(purchase_info, k)
                # 将可能为字符串的数值字段转换为整数
                if k in ['check_flow_id', 'archive_time', 'stop_time', 'void_time', 
                         'archive_uid', 'stop_uid', 'void_uid', 'check_time',
                         'create_time', 'update_time', 'delete_time', 'sign_time',
                         'start_time', 'end_time']:
                    try:
                        value = int(value) if value is not None else 0
                    except (ValueError, TypeError):
                        value = 0
                purchase_data[k] = value
        
        # 转换为驼峰命名
        from utils.camel_converter import to_camel
        purchase_data_camel = {}
        for key, value in purchase_data.items():
            camel_key = to_camel(key)
            purchase_data_camel[camel_key] = value
        
        # 查询关联信息
        # 1. 分类名称
        if purchase_info.cate_id and purchase_info.cate_id > 0:
            from module_admin.dao.contract_cate_dao import ContractCateDao
            try:
                cate_info = await ContractCateDao.get_contract_cate_detail_by_id(query_db, purchase_info.cate_id)
                if cate_info:
                    purchase_data_camel['cateName'] = cate_info.title
            except Exception as e:
                logger.error(f'查询采购合同分类名称失败: {e}')
        
        # 2. 创建人姓名
        if purchase_info.admin_id and purchase_info.admin_id > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(query_db, purchase_info.admin_id)
            if admin_result and admin_result.get('user_basic_info'):
                admin_info = admin_result['user_basic_info']
                purchase_data_camel['adminName'] = admin_info.nick_name or admin_info.user_name
        
        # 3. 制定人姓名
        if purchase_info.prepared_uid and purchase_info.prepared_uid > 0:
            from module_admin.dao.user_dao import UserDao
            prepared_result = await UserDao.get_user_by_id(query_db, purchase_info.prepared_uid)
            if prepared_result and prepared_result.get('user_basic_info'):
                prepared_info = prepared_result['user_basic_info']
                purchase_data_camel['preparedName'] = prepared_info.nick_name or prepared_info.user_name
        
        # 4. 签订人姓名
        if purchase_info.sign_uid and purchase_info.sign_uid > 0:
            from module_admin.dao.user_dao import UserDao
            sign_result = await UserDao.get_user_by_id(query_db, purchase_info.sign_uid)
            if sign_result and sign_result.get('user_basic_info'):
                sign_info = sign_result['user_basic_info']
                purchase_data_camel['signName'] = sign_info.nick_name or sign_info.user_name
        
        # 5. 保管人姓名
        if purchase_info.keeper_uid and purchase_info.keeper_uid > 0:
            from module_admin.dao.user_dao import UserDao
            keeper_result = await UserDao.get_user_by_id(query_db, purchase_info.keeper_uid)
            if keeper_result and keeper_result.get('user_basic_info'):
                keeper_info = keeper_result['user_basic_info']
                purchase_data_camel['keeperName'] = keeper_info.nick_name or keeper_info.user_name
        
        # 6. 部门名称
        if purchase_info.did and purchase_info.did > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_detail_by_id(query_db, purchase_info.did)
            if dept_info:
                purchase_data_camel['deptName'] = dept_info.dept_name
        
        # 添加客户字段别名
        purchase_data_camel['customerId'] = purchase_data_camel.get('supplierId')
        purchase_data_camel['customer'] = purchase_data_camel.get('supplier')
        
        # 格式化时间字段（直接在原字段上格式化，不添加Str后缀）
        # 日期字段：startTime, endTime, signTime
        for field in ['startTime', 'endTime', 'signTime']:
            val = purchase_data_camel.get(field)
            if val and int(val) > 0:
                purchase_data_camel[field] = timestamp_to_datetime(int(val), '%Y-%m-%d')
            else:
                purchase_data_camel[field] = None
        
        # 日期时间字段：createTime, updateTime, stopTime, voidTime, archiveTime, checkTime
        for field in ['createTime', 'updateTime', 'stopTime', 'voidTime', 'archiveTime', 'checkTime']:
            val = purchase_data_camel.get(field)
            if val and int(val) > 0:
                purchase_data_camel[field] = timestamp_to_datetime(int(val), '%Y-%m-%d %H:%M:%S')
            else:
                purchase_data_camel[field] = None
        
        # 添加审批记录
        flow_id = purchase_data_camel.get('checkFlowId', 0)
        if flow_id is not None:
            try:
                flow_id = int(flow_id)
            except (ValueError, TypeError):
                flow_id = 0
        
        if flow_id and flow_id > 0:
            records_raw = await FlowRecordDao.get_records_dict(query_db, purchase_id, flow_id)
            if records_raw:
                records = []
                for rec in records_raw:
                    check_time = rec.get('check_time')
                    # 确保check_time是整数类型
                    if check_time:
                        try:
                            check_time = int(check_time)
                        except (ValueError, TypeError):
                            check_time = None
                    
                    record_dict = {
                        'id': rec.get('id'),
                        'actionId': rec.get('action_id'),
                        'checkTable': rec.get('check_table'),
                        'flowId': rec.get('flow_id'),
                        'stepId': rec.get('step_id'),
                        'checkUid': rec.get('check_uid'),
                        'checkUser': rec.get('check_user'),
                        'checkTime': rec.get('check_time'),
                        'checkTimeStr': timestamp_to_datetime(check_time, '%Y-%m-%d %H:%M:%S') if check_time else None,
                        'checkStatus': rec.get('check_status'),
                        'checkStatusStr': cls._get_check_status_text(rec.get('check_status')),
                        'content': rec.get('content', ''),
                        'checkFiles': rec.get('check_files', '')
                    }
                    records.append(record_dict)
                purchase_data_camel['records'] = records
            else:
                purchase_data_camel['records'] = []
        else:
            purchase_data_camel['records'] = []
        
        return purchase_data_camel

    @staticmethod
    def _get_check_status_text(check_status: int | None) -> str:
        """
        获取审批状态文本
        
        :param check_status: 审批状态码
        :return: 状态文本
        """
        status_map = {
            0: '提交',
            1: '通过',
            2: '驳回',
            3: '撤销',
            4: '反确认'
        }
        return status_map.get(check_status, '未知')

    @classmethod
    async def archive_purchase_services(
            cls, request: Request, query_db: AsyncSession, purchase_id: int, current_user_id: int
    ) -> CrudResponseModel:
        """
        归档采购合同 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param purchase_id: 采购合同 ID
        :param current_user_id: 当前用户 ID（归档人）
        :return: 归档结果
        """
        try:
            # 检查合同是否存在
            existing_purchase = await PurchaseDao.get_by_id(query_db, purchase_id)
            if not existing_purchase:
                raise ServiceException(message='采购合同不存在')
            
            # 检查是否已经归档
            if existing_purchase.archive_time and existing_purchase.archive_time > 0:
                raise ServiceException(message='该合同已归档，无需重复操作')
            
            # 检查是否已中止或作废
            if existing_purchase.stop_time and existing_purchase.stop_time > 0:
                raise ServiceException(message='该合同已中止，无法归档')
            
            if existing_purchase.void_time and existing_purchase.void_time > 0:
                raise ServiceException(message='该合同已作废，无法归档')
            
            # 执行归档
            archive_time = int(datetime.now().timestamp())
            result = await PurchaseDao.archive_purchase(query_db, purchase_id, current_user_id, archive_time)
            
            if result > 0:
                logger.info(f'采购合同归档成功 - ID: {purchase_id}, 归档人: {current_user_id}')
                return CrudResponseModel(is_success=True, message='归档成功')
            else:
                raise ServiceException(message='归档失败')
        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'采购合同归档失败: {str(e)}', exc_info=True)
            raise e