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
from module_admin.entity.vo.contract_cate_vo import (
    AddContractCateModel,
    DeleteContractCateModel,
    EditContractCateModel,
    ContractCateModel,
    ContractCatePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.contract_cate_service import ContractCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

contract_cate_controller = APIRouterPro(
    prefix='/system/contractCate', order_num=22, tags=['1.6-系统管理 - 合同类别管理'], dependencies=[PreAuthDependency()]
)


@contract_cate_controller.get(
    '/list',
    summary='获取合同类别分页列表接口',
    description='用于获取合同类别分页列表',
    response_model=PageResponseModel[ContractCateModel],
    dependencies=[UserInterfaceAuthDependency('system:contractCate:list')],
)
async def get_system_contract_cate_list(
        request: Request,
        contract_cate_page_query: Annotated[ContractCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    contract_cate_page_query_result = await ContractCateService.get_contract_cate_list_services(
        query_db, contract_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=contract_cate_page_query_result)


@contract_cate_controller.post(
    '',
    summary='新增合同类别接口',
    description='用于新增合同类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contractCate:add')],
)
@ValidateFields(validate_model='add_contract_cate')
@Log(title='合同类别管理', business_type=BusinessType.INSERT)
async def add_system_contract_cate(
        request: Request,
        add_contract_cate: AddContractCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_contract_cate_result = await ContractCateService.add_contract_cate_services(request, query_db, add_contract_cate)
    logger.info(add_contract_cate_result.message)

    return ResponseUtil.success(msg=add_contract_cate_result.message)


@contract_cate_controller.put(
    '',
    summary='编辑合同类别接口',
    description='用于编辑合同类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contractCate:edit')],
)
@ValidateFields(validate_model='edit_contract_cate')
@Log(title='合同类别管理', business_type=BusinessType.UPDATE)
async def edit_system_contract_cate(
        request: Request,
        edit_contract_cate: EditContractCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_contract_cate_result = await ContractCateService.edit_contract_cate_services(request, query_db, edit_contract_cate)
    logger.info(edit_contract_cate_result.message)

    return ResponseUtil.success(msg=edit_contract_cate_result.message)


@contract_cate_controller.delete(
    '/{ids}',
    summary='删除合同类别接口',
    description='用于删除合同类别',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contractCate:remove')],
)
@Log(title='合同类别管理', business_type=BusinessType.DELETE)
async def delete_system_contract_cate(
        request: Request,
        ids: Annotated[str, Path(description='需要删除的合同类别 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_contract_cate = DeleteContractCateModel(ids=ids)
    delete_contract_cate_result = await ContractCateService.delete_contract_cate_services(
        request, query_db, delete_contract_cate
    )
    logger.info(delete_contract_cate_result.message)

    return ResponseUtil.success(msg=delete_contract_cate_result.message)


@contract_cate_controller.put(
    '/set',
    summary='设置合同类别状态接口',
    description='用于设置合同类别状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:contractCate:edit')],
)
@Log(title='合同类别管理', business_type=BusinessType.UPDATE)
async def set_system_contract_cate_status(
        request: Request,
        set_contract_cate: EditContractCateModel,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_contract_cate_result = await ContractCateService.set_contract_cate_status_services(
        request, query_db, set_contract_cate
    )
    logger.info(set_contract_cate_result.message)

    return ResponseUtil.success(msg=set_contract_cate_result.message)


@contract_cate_controller.get(
    '/{id}',
    summary='获取合同类别详情接口',
    description='用于获取指定合同类别的详细信息',
    response_model=DataResponseModel[ContractCateModel],
    dependencies=[UserInterfaceAuthDependency('system:contractCate:query')],
)
async def query_detail_system_contract_cate(
        request: Request,
        id: Annotated[int, Path(description='合同类别 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_contract_cate_result = await ContractCateService.contract_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_contract_cate_result)

