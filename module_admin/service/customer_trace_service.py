# 4. 创建 Service 文件：module_admin/service/customer_trace_service.py
from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.customer_trace_dao import CustomerTraceDao
from module_admin.entity.vo.customer_trace_vo import (
    AddCustomerTraceModel,
    DeleteCustomerTraceModel,
    EditCustomerTraceModel,
    CustomerTraceModel,
    CustomerTracePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class CustomerTraceService:
    """
    客户跟进记录管理服务层
    """

    @classmethod
    async def get_customer_trace_list_services(
            cls, query_db: AsyncSession, query_object: CustomerTracePageQueryModel,
            current_user_id: int, auth_dids: str = '', son_dids: str = '',
            is_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取客户跟进记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为管理员
        :param is_page: 是否开启分页
        :return: 客户跟进记录列表信息对象
        """
        trace_list_result = await CustomerTraceDao.get_customer_trace_list(
            query_db, query_object, current_user_id, auth_dids, son_dids, is_admin, is_page
        )

        return trace_list_result

    @classmethod
    async def add_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddCustomerTraceModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增客户跟进记录对象
        :param current_user_id: 当前用户 ID
        :return: 新增客户跟进记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            add_trace = CustomerTraceModel(
                cid=page_object.cid if page_object.cid is not None else 0,
                contact_id=page_object.contact_id if page_object.contact_id is not None else 0,
                chance_id=page_object.chance_id if page_object.chance_id is not None else 0,
                types=page_object.types if page_object.types is not None else 0,
                stage=page_object.stage if page_object.stage is not None else 0,
                content=page_object.content,
                follow_time=page_object.follow_time if page_object.follow_time is not None else 0,
                next_time=page_object.next_time if page_object.next_time is not None else 0,
                file_ids=page_object.file_ids if page_object.file_ids is not None else '',
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            await CustomerTraceDao.add_customer_trace_dao(query_db, add_trace)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditCustomerTraceModel
    ) -> CrudResponseModel:
        """
        编辑客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑客户跟进记录对象
        :return: 编辑客户跟进记录校验结果
        """
        edit_trace = page_object.model_dump(exclude_unset=True)
        trace_info = await cls.customer_trace_detail_services(query_db, page_object.id)

        if trace_info.id:
            try:
                edit_trace['update_time'] = int(datetime.now().timestamp())
                await CustomerTraceDao.edit_customer_trace_dao(query_db, edit_trace)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='跟进记录不存在')

    @classmethod
    async def delete_customer_trace_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteCustomerTraceModel
    ) -> CrudResponseModel:
        """
        删除客户跟进记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除客户跟进记录对象
        :return: 删除客户跟进记录校验结果
        """
        if page_object.id:
            try:
                trace = await cls.customer_trace_detail_services(query_db, page_object.id)
                if not trace.id:
                    raise ServiceException(message='跟进记录不存在')

                update_time = int(datetime.now().timestamp())
                await CustomerTraceDao.delete_customer_trace_dao(
                    query_db,
                    CustomerTraceModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入跟进记录 id 为空')

    @classmethod
    async def customer_trace_detail_services(cls, query_db: AsyncSession, trace_id: int) -> CustomerTraceModel:
        """
        获取客户跟进记录详细信息 service

        :param query_db: orm 对象
        :param trace_id: 跟进记录 ID
        :return: 跟进记录 ID 对应的信息
        """
        trace = await CustomerTraceDao.get_customer_trace_detail_by_id(query_db, trace_id)
        
        if trace:
            # 直接使用 ORM 对象，Pydantic 会自动处理 from_attributes
            result = CustomerTraceModel.model_validate(trace)
        else:
            result = CustomerTraceModel()

        return result

