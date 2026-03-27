from fastapi import File, Form, Path, Query, Request, Response, UploadFile
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from common.aspect.data_scope import DataScopeDependency
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from module_personnel.entity.do.rewards_do import OaRewards
from module_personnel.entity.vo.rewards_vo import OaRewardsBaseModel, OaRewardsPageQueryModel
from module_personnel.service.rewards_service import RewardsService

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
    query_object: OaRewardsPageQueryModel,
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaRewards)],
) -> Response:
    return await RewardsService.get_page_list_service(query_db,query_object,data_scope_sql,True)

@personnel_rewards_controller.get(
    "/add",
    summary='新增奖罚管理',
    description='用于新增奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:add')],
)
async def add_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    query_object: OaRewardsBaseModel,
) -> Response:
    return await RewardsService.add_service(query_db, query_object)

@personnel_rewards_controller.post(
    "/update",
    summary='更新奖罚管理',
    description='用于更新奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:update')],
)
async def update_profile(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: OaRewardsBaseModel,
)->Response:
    return await RewardsService().update_service(query_db, model)

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
    return await RewardsService.get_info_service(query_db, id)

@personnel_rewards_controller.get(
    "/delete/{id}",
    summary='删除奖罚管理',
    description='用于删除奖罚管理',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('humanresource:staff:archive:personnel:rewards:delete')],
)
async def delete_change(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    id: int,
) -> Response:
    return await RewardsService.del_by_id(query_db, id)
