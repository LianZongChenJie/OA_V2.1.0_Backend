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
            
            # 转换为字典并添加必要字段
            purchase_data = page_object.model_dump(exclude={"id", "create_time", "update_time"}, exclude_none=True)
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
                
                valid_fields = {c.name for c in OaPurchase.__table__.columns}
                exclude_fields = {'id', 'create_time', 'delete_time', 'admin_id'}
                
                purchase_data = {
                    k: v for k, v in page_object.model_dump(exclude_unset=True, by_alias=False).items()
                    if k in valid_fields and k not in exclude_fields
                }
                
                logger.info(f'采购合同编辑 - ID: {page_object.id}')
                logger.info(f'采购合同编辑 - 原始数据: {page_object.model_dump(exclude_unset=True, by_alias=False)}')
                logger.info(f'采购合同编辑 - 过滤后数据: {purchase_data}')
                
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
    async def purchase_detail_services(cls, query_db: AsyncSession, purchase_id: int) -> PurchaseModel:
        """
        获取采购合同详细信息 service

        :param query_db: orm 对象
        :param purchase_id: 采购合同 ID
        :return: 采购合同详细信息对象
        """
        from datetime import datetime as dt
        
        purchase_result = await PurchaseDao.get_by_id(query_db, purchase_id)
        
        if not purchase_result:
            return PurchaseModel()

        # 提取数据库表字段
        valid_fields = {c.name for c in OaPurchase.__table__.columns}
        purchase_data = {
            k: getattr(purchase_result, k)
            for k in valid_fields
            if hasattr(purchase_result, k)
        }

        # 格式化时间字段为字符串
        def format_timestamp_to_str(timestamp_value: int | None) -> str:
            """将时间戳转换为日期时间字符串"""
            if not timestamp_value or timestamp_value == 0:
                return ''
            try:
                return dt.fromtimestamp(timestamp_value).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                return ''
        
        # 添加格式化后的时间字符串字段
        purchase_data['startTimeStr'] = format_timestamp_to_str(purchase_data.get('start_time'))
        purchase_data['endTimeStr'] = format_timestamp_to_str(purchase_data.get('end_time'))
        purchase_data['signTimeStr'] = format_timestamp_to_str(purchase_data.get('sign_time'))
        purchase_data['createTimeStr'] = format_timestamp_to_str(purchase_data.get('create_time'))
        purchase_data['updateTimeStr'] = format_timestamp_to_str(purchase_data.get('update_time'))
        
        # 查询关联数据
        # 分类名称
        if purchase_data.get('cate_id') and purchase_data['cate_id'] > 0:
            from module_admin.dao.contract_cate_dao import ContractCateDao
            cate_info = await ContractCateDao.get_contract_cate_detail_by_id(query_db, purchase_data['cate_id'])
            if cate_info:
                purchase_data['cateName'] = cate_info.title
        
        # 创建人姓名
        if purchase_data.get('admin_id') and purchase_data['admin_id'] > 0:
            from module_admin.dao.user_dao import UserDao
            admin_result = await UserDao.get_user_by_id(query_db, purchase_data['admin_id'])
            if admin_result and admin_result.get('user_basic_info'):
                purchase_data['adminName'] = admin_result['user_basic_info'].nick_name or admin_result['user_basic_info'].user_name
        
        # 合同制定人姓名
        if purchase_data.get('prepared_uid') and purchase_data['prepared_uid'] > 0:
            from module_admin.dao.user_dao import UserDao
            prepared_result = await UserDao.get_user_by_id(query_db, purchase_data['prepared_uid'])
            if prepared_result and prepared_result.get('user_basic_info'):
                purchase_data['preparedName'] = prepared_result['user_basic_info'].nick_name or prepared_result['user_basic_info'].user_name
        
        # 合同签订人姓名
        if purchase_data.get('sign_uid') and purchase_data['sign_uid'] > 0:
            from module_admin.dao.user_dao import UserDao
            sign_result = await UserDao.get_user_by_id(query_db, purchase_data['sign_uid'])
            if sign_result and sign_result.get('user_basic_info'):
                purchase_data['signName'] = sign_result['user_basic_info'].nick_name or sign_result['user_basic_info'].user_name
        
        # 合同保管人姓名
        if purchase_data.get('keeper_uid') and purchase_data['keeper_uid'] > 0:
            from module_admin.dao.user_dao import UserDao
            keeper_result = await UserDao.get_user_by_id(query_db, purchase_data['keeper_uid'])
            if keeper_result and keeper_result.get('user_basic_info'):
                purchase_data['keeperName'] = keeper_result['user_basic_info'].nick_name or keeper_result['user_basic_info'].user_name
        
        # 部门名称
        if purchase_data.get('did') and purchase_data['did'] > 0:
            from module_admin.dao.dept_dao import DeptDao
            dept_info = await DeptDao.get_dept_by_id(query_db, purchase_data['did'])
            if dept_info:
                purchase_data['deptName'] = dept_info.dept_name
        
        result = PurchaseModel(**purchase_data)
        return result

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

