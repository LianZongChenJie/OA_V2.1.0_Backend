from fastapi import File, Form, Path, Query, Request, Response, UploadFile, Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.router import APIRouterPro
from module_personnel.entity.do.labor_contract_do import OaLaborContract
from module_personnel.entity.vo.lable_contract_vo import OaLaborContractBaseModel, OaLaborContractPageQueryModel
from module_personnel.service.labor_contrack_service import LaborContractService
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)


labor_contrack_controller = APIRouterPro(
    prefix='/personnel/contract', order_num=3, tags=['人事管理-员工合同'], dependencies=[PreAuthDependency()]
)

@labor_contrack_controller.get(
    "/list",
    summary='获取员工合同列表',
    description='用于获取员工合同列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:contract:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaLaborContractPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaLaborContract)],
) -> Response:
    result =  await LaborContractService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@labor_contrack_controller.post(
    "/add",
    summary='新增员工合同',
    description='用于新增员工合同',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:contract:add')],
)
async def add_labor_contract(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaLaborContractBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result =  await LaborContractService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@labor_contrack_controller.put(
    "/update",
    summary='更新员工合同',
    description='用于更新员工合同',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:contract:update')],
)
async def update_labor_contract(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaLaborContractBaseModel, Body()],
)->Response:
    result =  await LaborContractService().update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@labor_contrack_controller.get(
    "/detail/{id}",
    summary='获取员工合同详情',
    description='用于获取员工合同详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:contract:query')],
)
async def get_detail(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await LaborContractService.get_info_service(query_db, id)
    return ResponseUtil.success(data=ModelConverter.time_format(ModelConverter.to_dict(result)))

@labor_contrack_controller.delete(
    "/delete/{id}",
    summary='删除员工合同',
    description='用于删除员工合同',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:contract:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await LaborContractService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
