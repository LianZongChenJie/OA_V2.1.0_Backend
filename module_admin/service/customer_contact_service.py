from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.customer_contact_dao import CustomerContactDao
from module_admin.entity.vo.customer_contact_vo import (
    AddCustomerContactModel,
    DeleteCustomerContactModel,
    EditCustomerContactModel,
    CustomerContactModel,
    CustomerContactPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class CustomerContactService:
    """
    客户联系人管理服务层
    """

    @classmethod
    async def get_customer_contact_list_services(
            cls, query_db: AsyncSession, query_object: CustomerContactPageQueryModel, user_id: int,
            where_conditions: list = None, where_or_conditions: list = None, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取联系人列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param where_conditions: WHERE 条件列表
        :param where_or_conditions: WHERE OR 条件列表
        :param is_page: 是否开启分页
        :return: 联系人列表信息对象
        """
        from utils.time_format_util import timestamp_to_datetime
        
        contact_list_result = await CustomerContactDao.get_customer_contact_list(
            query_db, query_object, user_id, where_conditions, where_or_conditions, is_page
        )

        # 处理列表数据，添加时间格式化和客户名称
        if isinstance(contact_list_result, PageModel) and hasattr(contact_list_result, 'rows'):
            enhanced_rows = []
            for item in contact_list_result.rows:
                if isinstance(item, dict):
                    contact_dict = item.copy()
                else:
                    contact_dict = CamelCaseUtil.transform_result(item)
                
                # 格式化时间字段
                create_time = contact_dict.get('createTime') or contact_dict.get('create_time')
                if create_time and int(create_time) > 0:
                    contact_dict['createTimeStr'] = timestamp_to_datetime(int(create_time), '%Y-%m-%d %H:%M:%S')
                
                update_time = contact_dict.get('updateTime') or contact_dict.get('update_time')
                if update_time and int(update_time) > 0:
                    contact_dict['updateTimeStr'] = timestamp_to_datetime(int(update_time), '%Y-%m-%d %H:%M:%S')
                
                # 查询客户名称（如果 DAO 层没有返回）
                customer_name = contact_dict.get('customerName') or contact_dict.get('customer_name')
                if not customer_name:
                    cid = contact_dict.get('cid')
                    if cid and int(cid) > 0:
                        try:
                            from module_admin.entity.do.customer_do import OaCustomer
                            from sqlalchemy import select
                            customer_query = select(OaCustomer).where(OaCustomer.id == cid)
                            customer_info = (await query_db.execute(customer_query)).scalars().first()
                            if customer_info:
                                contact_dict['customerName'] = customer_info.name
                        except Exception as e:
                            from utils.log_util import logger
                            logger.error(f'查询客户名称失败: {e}')
                elif 'customer_name' in contact_dict:
                    # 如果存在 customer_name，转换为 customerName
                    contact_dict['customerName'] = contact_dict.pop('customer_name')
                
                enhanced_rows.append(contact_dict)
            contact_list_result.rows = enhanced_rows
        elif isinstance(contact_list_result, list):
            enhanced_list = []
            for item in contact_list_result:
                if isinstance(item, dict):
                    contact_dict = item.copy()
                else:
                    contact_dict = CamelCaseUtil.transform_result(item)
                
                # 格式化时间字段
                create_time = contact_dict.get('createTime') or contact_dict.get('create_time')
                if create_time and int(create_time) > 0:
                    contact_dict['createTimeStr'] = timestamp_to_datetime(int(create_time), '%Y-%m-%d %H:%M:%S')
                
                update_time = contact_dict.get('updateTime') or contact_dict.get('update_time')
                if update_time and int(update_time) > 0:
                    contact_dict['updateTimeStr'] = timestamp_to_datetime(int(update_time), '%Y-%m-%d %H:%M:%S')
                
                # 查询客户名称（如果 DAO 层没有返回）
                customer_name = contact_dict.get('customerName') or contact_dict.get('customer_name')
                if not customer_name:
                    cid = contact_dict.get('cid')
                    if cid and int(cid) > 0:
                        try:
                            from module_admin.entity.do.customer_do import OaCustomer
                            from sqlalchemy import select
                            customer_query = select(OaCustomer).where(OaCustomer.id == cid)
                            customer_info = (await query_db.execute(customer_query)).scalars().first()
                            if customer_info:
                                contact_dict['customerName'] = customer_info.name
                        except Exception as e:
                            from utils.log_util import logger
                            logger.error(f'查询客户名称失败: {e}')
                elif 'customer_name' in contact_dict:
                    # 如果存在 customer_name，转换为 customerName
                    contact_dict['customerName'] = contact_dict.pop('customer_name')
                
                enhanced_list.append(contact_dict)
            contact_list_result = enhanced_list

        return contact_list_result

    @classmethod
    async def check_contact_name_unique_services(
            cls, query_db: AsyncSession, page_object: CustomerContactModel
    ) -> bool:
        """
        校验联系人姓名是否唯一 service

        :param query_db: orm 对象
        :param page_object: 联系人对象
        :return: 校验结果
        """
        contact_id = -1 if page_object.id is None else page_object.id
        contact = await CustomerContactDao.get_customer_contact_by_info(query_db, page_object)
        if contact and contact.id != contact_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_customer_contact_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCustomerContactModel, user_id: int
    ) -> CrudResponseModel:
        """
        新增联系人信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增联系人对象
        :param user_id: 当前用户 ID
        :return: 新增联系人校验结果
        """
        # 校验联系人姓名是否唯一
        if not await cls.check_contact_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增联系人失败，该客户下联系人姓名已存在')
        
        try:
            current_time = int(datetime.now().timestamp())

            contact_data = page_object.model_dump(
                exclude_unset=True,
                exclude={
                    'id', 'customer_name', 'create_time', 'update_time', 'delete_time'
                }
            )

            contact_data['admin_id'] = user_id
            contact_data['create_time'] = current_time
            contact_data['update_time'] = current_time
            contact_data['delete_time'] = 0

            await CustomerContactDao.add_customer_contact_dao(query_db, CustomerContactModel(**contact_data))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_customer_contact_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCustomerContactModel
    ) -> CrudResponseModel:
        """
        编辑联系人信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑联系人对象
        :return: 编辑联系人校验结果
        """
        if page_object.id:
            # 校验联系人姓名是否唯一（排除自身）
            if not await cls.check_contact_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改联系人失败，该客户下联系人姓名已存在')
            
            try:
                edit_contact = page_object.model_dump(
                    exclude_unset=True,
                    exclude={
                        'id', 'customer_name', 'create_time', 'delete_time'
                    }
                )
                edit_contact['update_time'] = int(datetime.now().timestamp())
                await CustomerContactDao.edit_customer_contact_dao(query_db, page_object.id, edit_contact)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='联系人不存在')

    @classmethod
    async def delete_customer_contact_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCustomerContactModel
    ) -> CrudResponseModel:
        """
        删除联系人信息 service（逻辑删除）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除联系人对象
        :return: 删除联系人校验结果
        """
        if page_object.id:
            try:
                contact = await cls.customer_contact_detail_services(query_db, page_object.id)
                if not contact.id:
                    raise ServiceException(message='联系人不存在')

                update_time = int(datetime.now().timestamp())
                await CustomerContactDao.del_customer_contact_dao(
                    query_db,
                    CustomerContactModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入联系人 id 为空')

    @classmethod
    async def customer_contact_detail_services(cls, query_db: AsyncSession, contact_id: int) -> CustomerContactModel:
        """
        获取联系人详细信息 service

        :param query_db: orm 对象
        :param contact_id: 联系人 id
        :return: 联系人 id 对应的信息
        """
        contact_detail = await CustomerContactDao.get_customer_contact_detail_by_id(query_db, contact_id)

        if not contact_detail:
            return CustomerContactModel()

        contact_info = contact_detail.get('contact_info')
        result_dict = CamelCaseUtil.transform_result(contact_info)

        result = CustomerContactModel(**result_dict)

        return result

