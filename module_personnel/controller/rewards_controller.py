from fastapi import File, Form, Path, Query, Request, Response, UploadFile,Body
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.annotation.log_annotation import Log
from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency, CurrentUserDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from module_personnel.entity.do.rewards_do import OaRewards
from module_personnel.entity.vo.rewards_vo import OaRewardsBaseModel, OaRewardsPageQueryModel
from module_personnel.service.rewards_service import RewardsService
from utils.camel_converter import ModelConverter
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

personnel_rewards_controller = APIRouterPro(
    prefix='/personnel/rewards', order_num=3, tags=['人事管理-奖罚管理'], dependencies=[PreAuthDependency()]
)

@personnel_rewards_controller.get(
    "/list",
    summary='获取奖罚管理列表',
    description='用于获取奖罚管理列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:query')],
)
async def get_page_list(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaRewardsPageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaRewards)],
) -> Response:
    result =  await RewardsService.get_page_list_service(query_db,query_object,data_scope_sql,True)
    return ResponseUtil.success(model_content=result)

@personnel_rewards_controller.post(
    "/add",
    summary='新增奖罚管理',
    description='用于新增奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:add')],
)
@Log(title='奖罚管理-新增', business_type=BusinessType.INSERT)
async def add_reward(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: Annotated[OaRewardsBaseModel, Body()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    query_object.admin_id = current_user.user.user_id
    result =  await RewardsService.add_service(query_db, query_object)
    return ResponseUtil.success(msg=result.message)

@personnel_rewards_controller.put(
    "/update",
    summary='更新奖罚管理',
    description='用于更新奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:update')],
)
@Log(title='奖罚管理-编辑', business_type=BusinessType.UPDATE)
async def update_reward(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaRewardsBaseModel, Body()],
)->Response:
    result =  await RewardsService.update_service(query_db, model)
    return ResponseUtil.success(msg=result.message)

@personnel_rewards_controller.get(
    "/detail/{id}",
    summary='获取奖罚管理详情',
    description='用于获取奖罚管理详情',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:query')],
)
async def get_detail(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await RewardsService.get_info_service(query_db, id)
    return ResponseUtil.success(data=result)

@personnel_rewards_controller.delete(
    "/delete/{id}",
    summary='删除奖罚管理',
    description='用于删除奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:delete')],
)
@Log(title='奖罚管理-删除', business_type=BusinessType.DELETE)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    result =  await RewardsService.del_by_id(query_db, id)
    return ResponseUtil.success(msg=result.message)
