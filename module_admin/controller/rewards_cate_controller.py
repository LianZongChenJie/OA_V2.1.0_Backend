from datetime import datetime
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
from module_admin.entity.vo.rewards_cate_vo import (
    AddRewardsCateModel,
    DeleteRewardsCateModel,
    EditRewardsCateModel,
    RewardsCateModel,
    RewardsCatePageQueryModel,
)
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.rewards_cate_service import RewardsCateService
from utils.log_util import logger
from utils.response_util import ResponseUtil

rewards_cate_controller = APIRouterPro(
    prefix='/system/rewardsCate', order_num=20, tags=['系统管理 - 奖罚项目管理'], dependencies=[PreAuthDependency()]
)


@rewards_cate_controller.get(
    '/list',
    summary='获取奖罚项目分页列表接口',
    description='用于获取奖罚项目分页列表',
    response_model=PageResponseModel[RewardsCateModel],
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:list')],
)
async def get_system_rewards_cate_list(
        request: Request,
        rewards_cate_page_query: Annotated[RewardsCatePageQueryModel, Query()],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    rewards_cate_page_query_result = await RewardsCateService.get_rewards_cate_list_services(
        query_db, rewards_cate_page_query, is_page=True
    )
    logger.info('获取成功')

    return ResponseUtil.success(model_content=rewards_cate_page_query_result)


@rewards_cate_controller.post(
    '',
    summary='新增奖罚项目接口',
    description='用于新增奖罚项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:add')],
)
@ValidateFields(validate_model='add_rewards_cate')
@Log(title='奖罚项目管理', business_type=BusinessType.INSERT)
async def add_system_rewards_cate(
    request: Request,
    add_rewards_cate: AddRewardsCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    add_rewards_cate_result = await RewardsCateService.add_rewards_cate_services(request, query_db, add_rewards_cate)
    logger.info(add_rewards_cate_result.message)

    return ResponseUtil.success(msg=add_rewards_cate_result.message)


@rewards_cate_controller.put(
    '',
    summary='编辑奖罚项目接口',
    description='用于编辑奖罚项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:edit')],
)
@ValidateFields(validate_model='edit_rewards_cate')
@Log(title='奖罚项目管理', business_type=BusinessType.UPDATE)
async def edit_system_rewards_cate(
    request: Request,
    edit_rewards_cate: EditRewardsCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    edit_rewards_cate_result = await RewardsCateService.edit_rewards_cate_services(request, query_db, edit_rewards_cate)
    logger.info(edit_rewards_cate_result.message)

    return ResponseUtil.success(msg=edit_rewards_cate_result.message)


@rewards_cate_controller.delete(
    '/{ids}',
    summary='删除奖罚项目接口',
    description='用于删除奖罚项目',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:remove')],
)
@Log(title='奖罚项目管理', business_type=BusinessType.DELETE)
async def delete_system_rewards_cate(
    request: Request,
    ids: Annotated[str, Path(description='需要删除的奖罚项目 ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_rewards_cate = DeleteRewardsCateModel(ids=ids)
    delete_rewards_cate_result = await RewardsCateService.delete_rewards_cate_services(
        request, query_db, delete_rewards_cate
    )
    logger.info(delete_rewards_cate_result.message)

    return ResponseUtil.success(msg=delete_rewards_cate_result.message)


@rewards_cate_controller.put(
    '/set',
    summary='设置奖罚项目状态接口',
    description='用于设置奖罚项目状态（禁用/启用）',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:edit')],
)
@Log(title='奖罚项目管理', business_type=BusinessType.UPDATE)
async def set_system_rewards_cate_status(
    request: Request,
    set_rewards_cate: EditRewardsCateModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    set_rewards_cate_result = await RewardsCateService.set_rewards_cate_status_services(
        request, query_db, set_rewards_cate
    )
    logger.info(set_rewards_cate_result.message)

    return ResponseUtil.success(msg=set_rewards_cate_result.message)


@rewards_cate_controller.get(
    '/{id}',
    summary='获取奖罚项目详情接口',
    description='用于获取指定奖罚项目的详细信息',
    response_model=DataResponseModel[RewardsCateModel],
    dependencies=[UserInterfaceAuthDependency('system:rewardsCate:query')],
)
async def query_detail_system_rewards_cate(
        request: Request,
        id: Annotated[int, Path(description='奖罚项目 ID')],
        query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    detail_rewards_cate_result = await RewardsCateService.rewards_cate_detail_services(query_db, id)
    logger.info(f'获取 id 为{id}的信息成功')

    return ResponseUtil.success(data=detail_rewards_cate_result)
