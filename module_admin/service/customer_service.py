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
from utils.log_util import logger


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

            # 只提取数据库中存在的字段
            customer_data = {
                'name': page_object.name,
                'source_id': page_object.source_id if page_object.source_id is not None else 0,
                'grade_id': page_object.grade_id if page_object.grade_id is not None else 0,
                'industry_id': page_object.industry_id if page_object.industry_id is not None else 0,
                'services_id': page_object.services_id if page_object.services_id is not None else 0,
                'provinceid': page_object.provinceid if page_object.provinceid is not None else 0,
                'cityid': page_object.cityid if page_object.cityid is not None else 0,
                'distid': page_object.distid if page_object.distid is not None else 0,
                'townid': page_object.townid if page_object.townid is not None else 0,
                'address': page_object.address if page_object.address is not None else '',
                'customer_status': page_object.customer_status if page_object.customer_status is not None else 0,
                'intent_status': page_object.intent_status if page_object.intent_status is not None else 0,
                'contact_first': page_object.contact_first if page_object.contact_first is not None else 0,
                'admin_id': user_id,
                'belong_uid': page_object.belong_uid if page_object.belong_uid and page_object.belong_uid != 0 else user_id,
                'belong_did': page_object.belong_did if page_object.belong_did is not None else 0,
                'belong_time': page_object.belong_time if page_object.belong_time is not None else 0,
                'distribute_time': page_object.distribute_time if page_object.distribute_time is not None else 0,
                'follow_time': page_object.follow_time if page_object.follow_time is not None else 0,
                'next_time': page_object.next_time if page_object.next_time is not None else 0,
                'discard_time': 0,
                'share_ids': page_object.share_ids if page_object.share_ids is not None else '',
                'content': page_object.content if page_object.content is not None else '',
                'market': page_object.market if page_object.market is not None else '',
                'remark': page_object.remark if page_object.remark is not None else '',
                'tax_bank': page_object.tax_bank if page_object.tax_bank is not None else '',
                'tax_banksn': page_object.tax_banksn if page_object.tax_banksn is not None else '',
                'tax_num': page_object.tax_num if page_object.tax_num is not None else '',
                'tax_mobile': page_object.tax_mobile if page_object.tax_mobile is not None else '',
                'tax_address': page_object.tax_address if page_object.tax_address is not None else '',
                'is_lock': page_object.is_lock if page_object.is_lock is not None else 0,
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
            }

            logger.info(f'准备插入数据库的数据 - source_id: {customer_data.get("source_id")}, grade_id: {customer_data.get("grade_id")}, industry_id: {customer_data.get("industry_id")}, belong_uid: {customer_data.get("belong_uid")}, belong_did: {customer_data.get("belong_did")}, share_ids: {customer_data.get("share_ids")}')

            # 新增客户
            new_customer = await CustomerDao.add_customer_dao(query_db, customer_data)

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
        编辑客户信息 service（支持修改联系人信息）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑客户对象
        :return: 编辑客户校验结果
        """
        if not page_object.id:
            raise ServiceException(message='客户不存在')

        # 校验客户名称是否唯一（排除自身）
        if not await cls.check_customer_name_unique_services(query_db, page_object):
            raise ServiceException(message='修改客户失败，客户名称已存在')

        try:
            from sqlalchemy import update as sql_update
            from module_admin.entity.do.customer_contact_do import OaCustomerContact
            
            current_time = int(datetime.now().timestamp())
            customer_id = page_object.id

            # ====================== 1. 更新客户基础信息 ======================
            edit_customer = page_object.model_dump(
                by_alias=False,
                exclude_unset=True,
                exclude={
                    'id', 'contact_info',
                    'belong_name', 'belong_department', 'industry', 'grade',
                    'source', 'customer_status_name', 'intent_status_name',
                    'follow_time_str', 'next_time_str', 'create_time_str',
                    'contact_name', 'contact_mobile', 'contact_email',
                    'share_names', 'delete_time', 'discard_time',
                    'belong_time_str', 'distribute_time_str', 'update_time_str'
                }
            )
            edit_customer['update_time'] = current_time
            await CustomerDao.edit_customer_dao(query_db, customer_id, edit_customer)

            # ====================== 2. 处理联系人：先删后加 ======================
            if page_object.contact_info and page_object.contact_info.name:
                # 1）逻辑删除该客户原有所有联系人
                await query_db.execute(
                    sql_update(OaCustomerContact)
                    .where(
                        OaCustomerContact.cid == customer_id,
                        OaCustomerContact.delete_time == 0
                    )
                    .values(delete_time=current_time)
                )

                # 2）重新插入新的联系人
                contact_data = {
                    'cid': customer_id,
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
                    'admin_id': 0,
                    'create_time': current_time,
                    'update_time': current_time,
                    'delete_time': 0,
                }
                db_contact = OaCustomerContact(**contact_data)
                query_db.add(db_contact)
                await query_db.flush()

                # 3）更新客户表第一联系人ID
                await CustomerDao.edit_customer_dao(
                    query_db, customer_id, {'contact_first': db_contact.id}
                )

            # 提交事务
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')

        except Exception as e:
            await query_db.rollback()
            raise e

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
        from utils.time_format_util import timestamp_to_datetime
        from module_admin.entity.vo.customer_vo import CustomerContactInfoModel
        
        customer_detail = await CustomerDao.get_customer_detail_by_id(query_db, customer_id)

        if not customer_detail:
            return CustomerModel()

        customer_info = customer_detail.get('customer_info')
        result_dict = CamelCaseUtil.transform_result(customer_info)
        
        result_dict['belongName'] = customer_detail.get('belong_name') or ''
        result_dict['belongDepartment'] = customer_detail.get('belong_department') or ''
        result_dict['industry'] = customer_detail.get('industry') or ''
        result_dict['grade'] = customer_detail.get('grade') or ''
        result_dict['source'] = customer_detail.get('source') or ''
        result_dict['customerStatusName'] = customer_detail.get('customer_status_name') or ''
        result_dict['intentStatusName'] = customer_detail.get('intent_status_name') or ''
        result_dict['contactName'] = customer_detail.get('contact_name') or ''
        result_dict['contactMobile'] = customer_detail.get('contact_mobile') or ''
        result_dict['contactEmail'] = customer_detail.get('contact_email') or ''
        result_dict['shareNames'] = customer_detail.get('share_names') or ''
        
        contact_list = customer_detail.get('contact_list', [])
        result_dict['contactList'] = contact_list
        
        if contact_list:
            first_contact = contact_list[0]
            result_dict['contactInfo'] = CustomerContactInfoModel(
                name=first_contact.get('name'),
                sex=first_contact.get('sex', 0),
                mobile=first_contact.get('mobile'),
                qq=first_contact.get('qq'),
                wechat=first_contact.get('wechat'),
                email=first_contact.get('email'),
                nickname=first_contact.get('nickname'),
                department=first_contact.get('department'),
                position=first_contact.get('position'),
                birthday=first_contact.get('birthday'),
                address=first_contact.get('address'),
            )
        else:
            result_dict['contactInfo'] = None
        
        follow_time = customer_info.follow_time
        if follow_time and int(follow_time) > 0:
            result_dict['followTimeStr'] = timestamp_to_datetime(int(follow_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['followTimeStr'] = ''
        
        next_time = customer_info.next_time
        if next_time and int(next_time) > 0:
            result_dict['nextTimeStr'] = timestamp_to_datetime(int(next_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['nextTimeStr'] = ''
        
        create_time = customer_info.create_time
        if create_time and int(create_time) > 0:
            result_dict['createTimeStr'] = timestamp_to_datetime(int(create_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['createTimeStr'] = ''
        
        belong_time = customer_info.belong_time
        if belong_time and int(belong_time) > 0:
            result_dict['belongTimeStr'] = timestamp_to_datetime(int(belong_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['belongTimeStr'] = ''
        
        distribute_time = customer_info.distribute_time
        if distribute_time and int(distribute_time) > 0:
            result_dict['distributeTimeStr'] = timestamp_to_datetime(int(distribute_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['distributeTimeStr'] = ''
        
        update_time = customer_info.update_time
        if update_time and int(update_time) > 0:
            result_dict['updateTimeStr'] = timestamp_to_datetime(int(update_time), '%Y-%m-%d %H:%M:%S')
        else:
            result_dict['updateTimeStr'] = ''

        result = CustomerModel(**result_dict)

        return result
