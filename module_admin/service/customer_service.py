from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.customer_dao import CustomerDao
from module_admin.entity.vo.customer_vo import (
    AddCustomerModel,
    DeleteCustomerModel,
    EditCustomerModel,
    CustomerModel,
    CustomerPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class CustomerService:
    """
    客户管理服务层
    """

    @classmethod
    async def get_customer_list_services(
            cls, query_db: AsyncSession, query_object: CustomerPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取客户列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 客户列表信息对象
        """
        customer_list_result = await CustomerDao.get_customer_list(query_db, query_object, user_id, is_page)

        return CamelCaseUtil.transform_result(customer_list_result)

    @classmethod
    async def check_customer_name_unique_services(
            cls, query_db: AsyncSession, page_object: CustomerModel
    ) -> bool:
        """
        校验客户名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 客户对象
        :return: 校验结果
        """
        customer_id = -1 if page_object.id is None else page_object.id
        customer = await CustomerDao.get_customer_detail_by_info(query_db, page_object)
        if customer and customer.id != customer_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_customer_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCustomerModel, user_id: int
    ) -> CrudResponseModel:
        """
        新增客户信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增客户对象
        :param user_id: 当前用户 ID
        :return: 新增客户校验结果
        """
        # 校验客户名称是否唯一
        if not await cls.check_customer_name_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增客户失败，客户名称已存在')
        
        try:
            current_time = int(datetime.now().timestamp())

            customer_data = page_object.model_dump(
                exclude_unset=True,
                exclude={
                    'id', 'belong_name', 'belong_department', 'industry', 'grade',
                    'source', 'customer_status_name', 'intent_status_name',
                    'follow_time_str', 'next_time_str', 'contact_name', 'contact_mobile',
                    'contact_email', 'share_names', 'create_time', 'update_time',
                    'delete_time', 'discard_time', 'contact_info'
                }
            )

            customer_data['admin_id'] = user_id
            customer_data['belong_uid'] = user_id
            customer_data['create_time'] = current_time
            customer_data['update_time'] = current_time
            customer_data['delete_time'] = 0
            customer_data['discard_time'] = 0

            # 新增客户
            new_customer = await CustomerDao.add_customer_dao(query_db, CustomerModel(**customer_data))
            
            # 如果有联系人信息，创建默认联系人
            if page_object.contact_info and page_object.contact_info.name:
                from module_admin.entity.do.customer_contact_do import OaCustomerContact
                
                contact_data = {
                    'cid': new_customer.id,
                    'is_default': 1,
                    'name': page_object.contact_info.name,
                    'sex': page_object.contact_info.sex if page_object.contact_info.sex is not None else 0,
                    'mobile': page_object.contact_info.mobile or '',
                    'qq': page_object.contact_info.qq or '',
                    'wechat': page_object.contact_info.wechat or '',
                    'email': page_object.contact_info.email or '',
                    'nickname': page_object.contact_info.nickname or '',
                    'department': page_object.contact_info.department or '',
                    'position': page_object.contact_info.position or '',
                    'birthday': page_object.contact_info.birthday or '',
                    'address': page_object.contact_info.address or '',
                    'family': '',
                    'admin_id': user_id,
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                }
                
                db_contact = OaCustomerContact(**contact_data)
                query_db.add(db_contact)
                await query_db.flush()
                
                # 更新客户的第一联系人ID
                customer_data['contact_first'] = db_contact.id
                await CustomerDao.edit_customer_dao(query_db, new_customer.id, {'contact_first': db_contact.id})
            
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_customer_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCustomerModel
    ) -> CrudResponseModel:
        """
        编辑客户信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑客户对象
        :return: 编辑客户校验结果
        """
        if page_object.id:
            # 校验客户名称是否唯一（排除自身）
            if not await cls.check_customer_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改客户失败，客户名称已存在')
            
            try:
                edit_customer = page_object.model_dump(
                    exclude_unset=True,
                    exclude={
                        'id', 'belong_name', 'belong_department', 'industry', 'grade',
                        'source', 'customer_status_name', 'intent_status_name',
                        'follow_time_str', 'next_time_str', 'contact_name', 'contact_mobile',
                        'contact_email', 'share_names', 'create_time', 'delete_time', 'discard_time'
                    }
                )
                edit_customer['update_time'] = int(datetime.now().timestamp())
                await CustomerDao.edit_customer_dao(query_db, page_object.id, edit_customer)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='客户不存在')

    @classmethod
    async def delete_customer_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCustomerModel
    ) -> CrudResponseModel:
        """
        删除客户信息 service（逻辑删除，使用 discard_time）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除客户对象
        :return: 删除客户校验结果
        """
        if page_object.id:
            try:
                customer = await cls.customer_detail_services(query_db, page_object.id)
                if not customer.id:
                    raise ServiceException(message='客户不存在')

                update_time = int(datetime.now().timestamp())
                await CustomerDao.discard_customer_dao(
                    query_db,
                    CustomerModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入客户 id 为空')

    @classmethod
    async def customer_detail_services(cls, query_db: AsyncSession, customer_id: int) -> CustomerModel:
        """
        获取客户详细信息 service

        :param query_db: orm 对象
        :param customer_id: 客户 id
        :return: 客户 id 对应的信息
        """
        customer_detail = await CustomerDao.get_customer_detail_by_id(query_db, customer_id)

        if not customer_detail:
            return CustomerModel()

        customer_info = customer_detail.get('customer_info')
        result_dict = CamelCaseUtil.transform_result(customer_info)

        result = CustomerModel(**result_dict)

        return result
