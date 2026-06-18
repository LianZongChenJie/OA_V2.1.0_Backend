from typing import Annotated

from fastapi import Path, Query, Request, Response
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_contract.entity.vo.contract_vo import (
    AddContractModel,
    DeleteContractModel,
    EditContractModel,
    ContractModel,
    ContractPageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_contract.service.contract_service import ContractService
from utils.camel_converter import ModelConverter
from utils.log_util import logger
from utils.response_util import ResponseUtil

contract_controller = APIRouterPro(
    prefix='/system/contract', order_num=30, tags=['系统管理 - 合同管理'], dependencies=[PreAuthDependency()]
)


@contract_controller.get(
    '/list',
    summary='获取合同分页列表接口',
    description='用于获取合同分页列表',
    response_model=PageResponseModel[ContractModel],
    dependencies=[UserInterfaceAuthDependency('system:contract:list')],
)
async def get_system_contract_list(
        request: Request,
        contract_page_query: Annotated[ContractPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 获取分页数据
    contract_page_query_result = await ContractService.get_contract_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_contract_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@contract_controller.get(
    '/archivelist',
    summary='获取合同归档分页列表接口',
    description='用于获取已归档的合同分页列表',
    response_model=PageResponseModel[ContractModel],
    dependencies=[UserInterfaceAuthDependency('system:contract:list')],
)
async def get_system_contract_archive_list(
        request: Request,
        contract_page_query: Annotated[ContractPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 设置归档状态为 1（已归档）
    contract_page_query.archive_status = 1
    
    # 获取分页数据
    contract_page_query_result = await ContractService.get_contract_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_contract_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@contract_controller.get(
    '/stoplist',
    summary='获取合同中止分页列表接口',
    description='用于获取已中止的合同分页列表',
    response_model=PageResponseModel[ContractModel],
    dependencies=[UserInterfaceAuthDependency('system:contract:list')],
)
async def get_system_contract_stop_list(
        request: Request,
        contract_page_query: Annotated[ContractPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 设置中止状态为 1（已中止）
    contract_page_query.stop_status = 1
    
    # 获取分页数据
    contract_page_query_result = await ContractService.get_contract_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_contract_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@contract_controller.get(
    '/voidlist',
    summary='获取合同作废分页列表接口',
    description='用于获取已作废的合同分页列表',
    response_model=PageResponseModel[ContractModel],
    dependencies=[UserInterfaceAuthDependency('system:contract:list')],
)
async def get_system_contract_void_list(
        request: Request,
        contract_page_query: Annotated[ContractPageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    # 设置作废状态为 1（已作废）
    contract_page_query.void_status = 1
    
    # 获取分页数据
    contract_page_query_result = await ContractService.get_contract_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_contract_admin 需要根据实际权限判断
        is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@contract_controller.post(
    '',
    summary='新增合同接口',
    description='用于新增合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:add')],
)
@ValidateFields(validate_model='add_contract')
@Log(title='合同管理', business_type=BusinessType.INSERT)
async def add_system_contract(
        request: Request,
        add_contract: AddContractModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_contract_result = await ContractService.add_contract_services(
        request, query_db, add_contract, current_user.user.user_id
    )
    logger.info(add_contract_result.message)

    return ResponseUtil.success(msg=add_contract_result.message)


@contract_controller.put(
    '',
    summary='编辑合同接口',
    description='用于编辑合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:edit')],
)
@ValidateFields(validate_model='edit_contract')
@Log(title='合同管理', business_type=BusinessType.UPDATE)
async def edit_system_contract(
        request: Request,
        edit_contract: EditContractModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_contract_result = await ContractService.edit_contract_services(
        request, query_db, edit_contract
    )
    logger.info(edit_contract_result.message)

    return ResponseUtil.success(msg=edit_contract_result.message)


@contract_controller.delete(
    '/{id}',
    summary='删除合同接口',
    description='用于删除合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:remove')],
)
@Log(title='合同管理', business_type=BusinessType.DELETE)
async def delete_system_contract(
        request: Request,
        id: Annotated[int, Path(description='需要删除的合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_contract = DeleteContractModel(id=id)
    delete_contract_result = await ContractService.delete_contract_services(
        request, query_db, delete_contract
    )
    logger.info(delete_contract_result.message)

    return ResponseUtil.success(msg=delete_contract_result.message)


@contract_controller.get(
    '/{id}',
    summary='获取合同详情接口',
    description='用于获取指定合同的详细信息',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('system:contract:query')],
)
async def query_detail_system_contract(
        request: Request,
        id: Annotated[int, Path(description='合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """获取合同详情"""
    try:
        contract_detail = await ContractService.contract_detail_services(query_db, id)
        logger.info(f'获取合同详情成功，ID：{id}')

        if contract_detail and isinstance(contract_detail, dict):
            # 将 contract 和 attachments 中的字段转换为驼峰命名
            from utils.common_util import CamelCaseUtil
            result = {}
            # 将合同信息字段直接放到result根级别
            if 'contract' in contract_detail:
                contract_data = CamelCaseUtil.transform_result(contract_detail['contract'])
                result.update(contract_data)
            # 附件作为同级字段
            if 'attachments' in contract_detail:
                result['attachments'] = CamelCaseUtil.transform_result(contract_detail['attachments'])
            return ResponseUtil.success(data=result)
        elif contract_detail and hasattr(contract_detail, 'model_dump'):
            return ResponseUtil.success(data=contract_detail.model_dump(by_alias=True))
        return ResponseUtil.success(data=contract_detail)
    except ServiceException as e:
        logger.error(f'获取合同详情失败：{e.message}')
        return ResponseUtil.error(msg=e.message)
    except Exception as e:
        logger.error(f'获取合同详情失败：{str(e)}', exc_info=True)
        return ResponseUtil.error(msg=f'获取详情失败：{str(e)}')