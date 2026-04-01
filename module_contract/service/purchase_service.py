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
                # 检查采购合同是否存在
                existing_purchase = await PurchaseDao.get_by_id(query_db, page_object.id)
                if not existing_purchase:
                    raise ServiceException(message='采购合同不存在')

                # 验重：检查合同名称是否与其他记录重复
                if not await cls.check_purchase_name_unique_services(query_db, page_object):
                    raise ServiceException(message='合同名称已存在')

                # 设置更新时间
                current_time = int(datetime.now().timestamp())
                
                # 转换为字典并更新
                purchase_data = page_object.model_dump(exclude={"create_time", "update_time"}, exclude_none=True)
                purchase_data['update_time'] = current_time
                
                await PurchaseDao.update(query_db, purchase_data)
                return CrudResponseModel(is_success=True, message='修改成功')
            except Exception as e:
                await query_db.rollback()
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

        # 添加扩展字段（需要从关联表查询）
        # TODO: 这里可以添加关联表查询逻辑，如分类名称、供应商名称、人员姓名等
        
        result = PurchaseModel(**purchase_data)
        return result

