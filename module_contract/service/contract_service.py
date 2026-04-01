# module_contract/service/contract_service.py
from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_contract.dao.contract_dao import ContractDao
from module_contract.entity.do.contract_do import OaContract
from module_contract.entity.vo.contract_vo import (
    AddContractModel,
    DeleteContractModel,
    EditContractModel,
    ContractModel,
    ContractPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class ContractService:
    """
    销售合同管理服务层
    """

    @classmethod
    async def get_contract_list_services(
            cls, query_db: AsyncSession, query_object: ContractPageQueryModel,
            current_user_id: int, auth_dids: str = '', son_dids: str = '',
            is_admin: bool = False, is_contract_admin: bool = False, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取合同列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param current_user_id: 当前用户 ID
        :param auth_dids: 可见部门数据
        :param son_dids: 可见子部门数据
        :param is_admin: 是否为超级管理员
        :param is_contract_admin: 是否为合同管理员
        :param is_page: 是否开启分页
        :return: 合同列表信息对象
        """
        # 如果是合同管理员，不进行权限过滤
        if is_contract_admin:
            contract_list_result = await ContractDao.get_contract_list(
                query_db, query_object, current_user_id, '', '', True, is_page
            )
        else:
            contract_list_result = await ContractDao.get_contract_list(
                query_db, query_object, current_user_id, auth_dids, son_dids, is_admin, is_page
            )

        return contract_list_result

    @classmethod
    async def check_contract_name_unique_services(
            cls, query_db: AsyncSession, page_object: ContractModel
    ) -> bool:
        """
        校验合同名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 合同对象
        :return: 校验结果
        """
        contract_id = -1 if page_object.id is None else page_object.id
        contract = await ContractDao.get_contract_detail_by_info(query_db, page_object)
        if contract and contract.id != contract_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_contract_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddContractModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        新增合同信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增合同对象
        :param current_user_id: 当前用户 ID
        :return: 新增合同校验结果
        """
        try:
            # 检查销售机会是否已关联
            if page_object.chance_id and page_object.chance_id > 0:
                has_chance = await ContractDao.check_chance_exists(query_db, page_object.chance_id)
                if has_chance:
                    raise ServiceException(message='所选的机会线索已关联有销售合同，不支持关联多合同')

            # 校验合同名称是否唯一
            if not await cls.check_contract_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'新增合同失败，合同名称已存在')

            current_time = int(datetime.now().timestamp())

            # 只提取数据库表存在的字段，排除扩展字段
            contract_data = {
                'pid': page_object.pid if page_object.pid is not None else 0,
                'code': page_object.code if page_object.code is not None else '',
                'name': page_object.name,
                'cate_id': page_object.cate_id if page_object.cate_id is not None else 0,
                'types': page_object.types if page_object.types is not None else 1,
                'subject_id': page_object.subject_id if page_object.subject_id is not None else '',
                'customer_id': page_object.customer_id if page_object.customer_id is not None else 0,
                'chance_id': page_object.chance_id if page_object.chance_id is not None else 0,
                'customer': page_object.customer if page_object.customer is not None else '',
                'contact_name': page_object.contact_name if page_object.contact_name is not None else '',
                'contact_mobile': page_object.contact_mobile if page_object.contact_mobile is not None else '',
                'contact_address': page_object.contact_address if page_object.contact_address is not None else '',
                'start_time': page_object.start_time if page_object.start_time is not None else 0,
                'end_time': page_object.end_time if page_object.end_time is not None else 0,
                'admin_id': current_user_id,
                'prepared_uid': page_object.prepared_uid if page_object.prepared_uid is not None else 0,
                'sign_uid': page_object.sign_uid if page_object.sign_uid is not None else 0,
                'keeper_uid': page_object.keeper_uid if page_object.keeper_uid is not None else 0,
                'share_ids': page_object.share_ids if page_object.share_ids is not None else '',
                'file_ids': page_object.file_ids if page_object.file_ids is not None else '',
                'seal_ids': page_object.seal_ids if page_object.seal_ids is not None else '',
                'sign_time': page_object.sign_time if page_object.sign_time is not None else 0,
                'did': page_object.did if page_object.did is not None else 0,
                'cost': page_object.cost if page_object.cost is not None else 0.00,
                'content': page_object.content if page_object.content is not None else '',
                'is_tax': page_object.is_tax if page_object.is_tax is not None else 0,
                'tax': page_object.tax if page_object.tax is not None else 0.00,
                'remark': page_object.remark if page_object.remark is not None else '',
                'create_time': current_time,
                'update_time': current_time,
                'delete_time': 0,
                'check_status': page_object.check_status if page_object.check_status is not None else 0,
                'check_flow_id': page_object.check_flow_id if page_object.check_flow_id is not None else 0,
                'check_step_sort': page_object.check_step_sort if page_object.check_step_sort is not None else 0,
                'check_uids': page_object.check_uids if page_object.check_uids is not None else '',
                'check_last_uid': page_object.check_last_uid if page_object.check_last_uid is not None else '',
                'check_history_uids': page_object.check_history_uids if page_object.check_history_uids is not None else '',
                'check_copy_uids': page_object.check_copy_uids if page_object.check_copy_uids is not None else '',
                'check_time': page_object.check_time if page_object.check_time is not None else 0,
            }

            await ContractDao.add_contract_dao(query_db, contract_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_contract_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditContractModel
    ) -> CrudResponseModel:
        """
        编辑合同信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑合同对象
        :return: 编辑合同校验结果
        """
        if page_object.id:
            # 检查销售机会是否已关联（排除当前合同）
            if page_object.chance_id and page_object.chance_id > 0:
                has_chance = await ContractDao.check_chance_exists(query_db, page_object.chance_id, page_object.id)
                if has_chance:
                    raise ServiceException(message='所选的机会线索已关联有销售合同，不支持关联多合同')

            # 校验合同名称是否唯一（排除自身）
            if not await cls.check_contract_name_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改合同失败，合同名称已存在')
            
            try:
                # 只提取数据库表存在的字段，排除扩展字段和不需要更新的字段
                valid_fields = {c.name for c in OaContract.__table__.columns}
                exclude_fields = {'id', 'create_time', 'delete_time', 'admin_id'}
                
                edit_contract = {
                    k: v for k, v in page_object.model_dump(exclude_unset=True).items()
                    if k in valid_fields and k not in exclude_fields
                }
                
                contract_info = await cls.contract_detail_services(query_db, page_object.id)

                if contract_info and contract_info.id:
                    edit_contract['update_time'] = int(datetime.now().timestamp())
                    await ContractDao.edit_contract_dao(query_db, page_object.id, edit_contract)
                    await query_db.commit()
                    return CrudResponseModel(is_success=True, message='更新成功')
                else:
                    raise ServiceException(message='合同不存在')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='合同不存在')

    @classmethod
    async def contract_detail_services(cls, query_db: AsyncSession, contract_id: int) -> ContractModel:
        """
        获取合同详细信息 service

        :param query_db: orm 对象
        :param contract_id: 合同 ID
        :return: 合同 ID 对应的信息
        """
        contract_result = await ContractDao.get_contract_detail_by_id(query_db, contract_id)

        if not contract_result:
            return ContractModel()

        # 从字典中提取 contract_info（SQLAlchemy 对象）
        contract_info = contract_result.get('contract_info')

        if not contract_info:
            return ContractModel()

        # 只提取数据库表存在的字段，排除扩展字段
        valid_fields = {c.name for c in OaContract.__table__.columns}
        contract_data = {
            k: getattr(contract_info, k)
            for k in valid_fields
            if hasattr(contract_info, k)
        }

        # 添加扩展字段（从 DAO 层返回的结果中获取）
        contract_data['cate_title'] = contract_result.get('cate_title')
        contract_data['subject_title'] = contract_result.get('subject_title')
        contract_data['admin_name'] = contract_result.get('admin_name')
        contract_data['prepared_name'] = contract_result.get('prepared_name')
        contract_data['sign_name'] = contract_result.get('sign_name')
        contract_data['keeper_name'] = contract_result.get('keeper_name')
        contract_data['share_names'] = contract_result.get('share_names', [])
        contract_data['check_status_name'] = contract_result.get('check_status_name')

        result = ContractModel(**contract_data)

        return result

    @classmethod
    async def delete_contract_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteContractModel
    ) -> CrudResponseModel:
        """
        删除合同信息 service（逻辑删除）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除合同对象
        :return: 删除合同校验结果
        """
        if page_object.id:
            try:
                contract = await cls.contract_detail_services(query_db, page_object.id)
                if not contract.id:
                    raise ServiceException(message='合同不存在')

                update_time = int(datetime.now().timestamp())
                await ContractDao.delete_contract_dao(
                    query_db,
                    ContractModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入合同 id 为空')

