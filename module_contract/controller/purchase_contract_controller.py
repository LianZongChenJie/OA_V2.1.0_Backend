from typing import Annotated

from fastapi import Path, Query, Request, Response, Body
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_contract.entity.vo.purchase_vo import (
    AddPurchaseModel,
    DeletePurchaseModel,
    EditPurchaseModel,
    PurchaseModel,
    PurchasePageQueryModel,
)
from module_contract.service.purchase_service import PurchaseService
from module_contract.service.contract_service import ContractService
from utils.log_util import logger
from utils.response_util import ResponseUtil

# 采购合同专用路由前缀
purchase_contract_controller = APIRouterPro(
    prefix='/system/purchase',
    order_num=31,
    tags=['1系统管理 - 采购合同管理'],
    dependencies=[PreAuthDependency()]
)


@purchase_contract_controller.get(
    '/list',
    summary='获取采购合同分页列表接口',
    description='用于获取采购合同分页列表（普通合同）',
    response_model=PageResponseModel[PurchaseModel],
    dependencies=[UserInterfaceAuthDependency('system:purchase:list')],
)
async def get_purchase_contract_list(
        request: Request,
        contract_page_query: Annotated[PurchasePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取采购合同列表（未归档、未中止、未作废的正常合同）

    :param request: Request 对象
    :param contract_page_query: 查询参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 合同列表分页数据
    """
    # 确保状态标志为 0（正常状态）
    contract_page_query.archive_status = 0
    contract_page_query.stop_status = 0
    contract_page_query.void_status = 0

    # 获取分页数据
    contract_page_query_result = await PurchaseService.get_purchase_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        False,  # is_contract_admin 根据实际权限判断
        is_page=True
    )
    logger.info('获取采购合同列表成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@purchase_contract_controller.get(
    '/archive/list',
    summary='获取已归档采购合同分页列表接口',
    description='用于获取已归档的采购合同分页列表',
    response_model=PageResponseModel[PurchaseModel],
    dependencies=[UserInterfaceAuthDependency('system:purchase:archive')],
)
async def get_purchase_contract_archive_list(
        request: Request,
        contract_page_query: Annotated[PurchasePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取已归档的采购合同列表

    :param request: Request 对象
    :param contract_page_query: 查询参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 已归档合同列表分页数据
    """
    # 设置归档状态标志
    contract_page_query.archive_status = 1
    contract_page_query.stop_status = 0
    contract_page_query.void_status = 0

    # 获取分页数据
    contract_page_query_result = await PurchaseService.get_purchase_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        True,  # 合同管理员可以查看所有归档合同
        is_page=True
    )
    logger.info('获取已归档采购合同列表成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@purchase_contract_controller.get(
    '/stop/list',
    summary='获取已中止采购合同分页列表接口',
    description='用于获取已中止的采购合同分页列表',
    response_model=PageResponseModel[PurchaseModel],
    dependencies=[UserInterfaceAuthDependency('system:purchase:stop')],
)
async def get_purchase_contract_stop_list(
        request: Request,
        contract_page_query: Annotated[PurchasePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取已中止的采购合同列表

    :param request: Request 对象
    :param contract_page_query: 查询参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 已中止合同列表分页数据
    """
    # 设置中止状态标志
    contract_page_query.archive_status = 0
    contract_page_query.stop_status = 1
    contract_page_query.void_status = 0

    # 获取分页数据
    contract_page_query_result = await PurchaseService.get_purchase_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        True,  # 合同管理员可以查看所有中止合同
        is_page=True
    )
    logger.info('获取已中止采购合同列表成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@purchase_contract_controller.get(
    '/void/list',
    summary='获取已作废采购合同分页列表接口',
    description='用于获取已作废的采购合同分页列表',
    response_model=PageResponseModel[PurchaseModel],
    dependencies=[UserInterfaceAuthDependency('system:purchase:void')],
)
async def get_purchase_contract_void_list(
        request: Request,
        contract_page_query: Annotated[PurchasePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取已作废的采购合同列表

    :param request: Request 对象
    :param contract_page_query: 查询参数对象
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 已作废合同列表分页数据
    """
    # 设置作废状态标志
    contract_page_query.archive_status = 0
    contract_page_query.stop_status = 0
    contract_page_query.void_status = 1

    # 获取分页数据
    contract_page_query_result = await PurchaseService.get_purchase_list_services(
        query_db,
        contract_page_query,
        current_user.user.user_id,
        current_user.user.auth_dids or '',
        current_user.user.son_dids or '',
        current_user.user.admin,
        True,  # 合同管理员可以查看所有作废合同
        is_page=True
    )
    logger.info('获取已作废采购合同列表成功')

    return ResponseUtil.success(model_content=contract_page_query_result)


@purchase_contract_controller.post(
    '',
    summary='新增采购合同接口',
    description='用于新增采购合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchase:add')],
)
@ValidateFields(validate_model='add_contract')
@Log(title='采购合同管理', business_type=BusinessType.INSERT)
async def add_purchase_contract(
        request: Request,
        add_contract: AddPurchaseModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    新增采购合同

    :param request: Request 对象
    :param add_contract: 新增合同模型
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    add_contract_result = await PurchaseService.add_purchase_services(
        request, query_db, add_contract, current_user.user.user_id
    )
    logger.info(add_contract_result.message)

    return ResponseUtil.success(msg=add_contract_result.message)


@purchase_contract_controller.put(
    '',
    summary='编辑采购合同接口',
    description='用于编辑采购合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchase:edit')],
)
@ValidateFields(validate_model='edit_contract')
@Log(title='采购合同管理', business_type=BusinessType.UPDATE)
async def edit_purchase_contract(
        request: Request,
        edit_contract: EditPurchaseModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    编辑采购合同

    :param request: Request 对象
    :param edit_contract: 编辑合同模型
    :param query_db: 数据库会话
    :param current_user: 当前用户
    :return: 操作结果
    """
    edit_contract_result = await PurchaseService.edit_purchase_services(
        request, query_db, edit_contract
    )
    logger.info(edit_contract_result.message)

    return ResponseUtil.success(msg=edit_contract_result.message)


@purchase_contract_controller.delete(
    '/{id}',
    summary='删除采购合同接口',
    description='用于删除采购合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchase:remove')],
)
@Log(title='采购合同管理', business_type=BusinessType.DELETE)
async def delete_purchase_contract(
        request: Request,
        id: Annotated[int, Path(description='需要删除的采购合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    删除采购合同（逻辑删除）

    :param request: Request 对象
    :param id: 合同 ID
    :param query_db: 数据库会话
    :return: 操作结果
    """
    delete_contract = DeletePurchaseModel(id=id)
    delete_contract_result = await PurchaseService.delete_purchase_services(
        request, query_db, delete_contract
    )
    logger.info(delete_contract_result.message)

    return ResponseUtil.success(msg=delete_contract_result.message)


@purchase_contract_controller.get(
    '/{id}',
    summary='获取采购合同详情接口',
    description='用于获取指定采购合同的详细信息',
    response_model=DataResponseModel[PurchaseModel],
    dependencies=[UserInterfaceAuthDependency('system:purchase:query')],
)
async def get_purchase_contract_detail(
        request: Request,
        id: Annotated[int, Path(description='采购合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取采购合同详情

    :param request: Request 对象
    :param id: 合同 ID
    :param query_db: 数据库会话
    :return: 合同详情数据
    """
    detail_contract_result = await PurchaseService.purchase_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的采购合同信息成功')

    return ResponseUtil.success(data=detail_contract_result)


@purchase_contract_controller.put(
    '/archive',
    summary='统一归档合同接口',
    description='根据合同类型归档采购或销售合同',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchase:archive')],
)
@Log(title='合同归档管理', business_type=BusinessType.UPDATE)
async def archive_contract_unified(
        request: Request,
        contract_type: Annotated[str, Query(description='合同类型：purchase=采购合同, sale=销售合同')],
        contract_id: Annotated[int, Query(description='需要归档的合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    统一归档接口 - 根据类型判断是采购合同还是销售合同

    :param request: Request 对象
    :param contract_type: 合同类型（purchase/sale）
    :param contract_id: 合同 ID
    :param query_db: 数据库会话
    :param current_user: 当前用户（归档人）
    :return: 操作结果
    """
    if contract_type.lower() == 'purchase':
        # 采购合同归档
        archive_result = await PurchaseService.archive_purchase_services(
            request, query_db, contract_id, current_user.user.user_id
        )
    elif contract_type.lower() == 'sale':
        # 销售合同归档
        archive_result = await ContractService.archive_contract_services(
            request, query_db, contract_id, current_user.user.user_id
        )
    else:
        from exceptions.exception import ServiceException
        raise ServiceException(message=f'不支持的合同类型: {contract_type}，请使用 purchase 或 sale')
    
    logger.info(archive_result.message)
    return ResponseUtil.success(msg=archive_result.message)


@purchase_contract_controller.put(
    '/archive/{id}',
    summary='归档采购合同接口',
    description='用于将采购合同转入归档状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:purchase:archive')],
)
@Log(title='采购合同管理', business_type=BusinessType.UPDATE)
async def archive_purchase_contract(
        request: Request,
        id: Annotated[int, Path(description='需要归档的采购合同 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    归档采购合同

    :param request: Request 对象
    :param id: 合同 ID
    :param query_db: 数据库会话
    :param current_user: 当前用户（归档人）
    :return: 操作结果
    """
    archive_result = await PurchaseService.archive_purchase_services(
        request, query_db, id, current_user.user.user_id
    )
    logger.info(archive_result.message)

    return ResponseUtil.success(msg=archive_result.message)

