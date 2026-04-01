from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.customer_chance_dao import CustomerChanceDao
from module_admin.entity.vo.customer_chance_vo import (
    AddCustomerChanceModel,
    DeleteCustomerChanceModel,
    EditCustomerChanceModel,
    CustomerChanceModel,
    CustomerChancePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class CustomerChanceService:
    """
    客户机会管理服务层
    """

    @classmethod
    async def get_customer_chance_list_services(
            cls, query_db: AsyncSession, query_object: CustomerChancePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取客户机会列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 客户机会列表信息对象
        """
        chance_list_result = await CustomerChanceDao.get_customer_chance_list(query_db, query_object, is_page)

        return chance_list_result

    @classmethod
    async def check_customer_chance_title_unique_services(
            cls, query_db: AsyncSession, page_object: CustomerChanceModel
    ) -> bool:
        """
        校验客户机会主题是否唯一 service

        :param query_db: orm 对象
        :param page_object: 客户机会对象
        :return: 校验结果
        """
        chance_id = -1 if page_object.id is None else page_object.id
        chance = await CustomerChanceDao.get_customer_chance_detail_by_info(query_db, page_object)
        if chance and chance.id != chance_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_customer_chance_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCustomerChanceModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增客户机会信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增客户机会对象
        :param current_user_id: 当前用户 ID
        :return: 新增客户机会校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            add_chance = CustomerChanceModel(
                title=page_object.title,
                cid=page_object.cid if page_object.cid is not None else 0,
                contact_id=page_object.contact_id if page_object.contact_id is not None else 0,
                services_id=page_object.services_id if page_object.services_id is not None else 0,
                stage=page_object.stage if page_object.stage is not None else 0,
                content=page_object.content,
                discovery_time=page_object.discovery_time if page_object.discovery_time is not None else 0,
                expected_time=page_object.expected_time if page_object.expected_time is not None else 0,
                expected_amount=page_object.expected_amount if page_object.expected_amount is not None else 0.00,
                admin_id=current_user_id,
                belong_uid=page_object.belong_uid if page_object.belong_uid is not None else 0,
                assist_ids=page_object.assist_ids if page_object.assist_ids is not None else '',
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            await CustomerChanceDao.add_customer_chance_dao(query_db, add_chance)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_customer_chance_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCustomerChanceModel
    ) -> CrudResponseModel:
        """
        编辑客户机会信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑客户机会对象
        :return: 编辑客户机会校验结果
        """
        edit_chance = page_object.model_dump(exclude_unset=True)
        chance_info = await cls.customer_chance_detail_services(query_db, page_object.id)

        if chance_info.id:
            try:
                edit_chance['update_time'] = int(datetime.now().timestamp())
                await CustomerChanceDao.edit_customer_chance_dao(query_db, edit_chance)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='机会不存在')

    @classmethod
    async def delete_customer_chance_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCustomerChanceModel
    ) -> CrudResponseModel:
        """
        删除客户机会信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除客户机会对象
        :return: 删除客户机会校验结果
        """
        if page_object.id:
            try:
                chance = await cls.customer_chance_detail_services(query_db, page_object.id)
                if not chance.id:
                    raise ServiceException(message='机会不存在')

                update_time = int(datetime.now().timestamp())
                await CustomerChanceDao.delete_customer_chance_dao(
                    query_db,
                    CustomerChanceModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入机会 id 为空')

    @classmethod
    async def customer_chance_detail_services(cls, query_db: AsyncSession, chance_id: int) -> CustomerChanceModel:
        """
        获取客户机会详细信息 service

        :param query_db: orm 对象
        :param chance_id: 机会 ID
        :return: 机会 ID 对应的信息
        """
        chance = await CustomerChanceDao.get_customer_chance_detail_by_id(query_db, chance_id)
        result = CustomerChanceModel(**CamelCaseUtil.transform_result(chance)) if chance else CustomerChanceModel()

        return result
