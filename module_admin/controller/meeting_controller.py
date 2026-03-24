from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.service.meeting_service import MeetingRoomService, MeetingOrderService, MeetingRecordsService
from module_admin.entity.vo.meeting_vo import (
    MeetingRoomPageQueryModel,
    AddMeetingRoomModel,
    EditMeetingRoomModel,
    DeleteMeetingRoomModel,
    MeetingRoomStatusModel,
    MeetingOrderPageQueryModel,
    AddMeetingOrderModel,
    EditMeetingOrderModel,
    DeleteMeetingOrderModel,
    MeetingRecordsPageQueryModel,
    AddMeetingRecordsModel,
    EditMeetingRecordsModel,
    DeleteMeetingRecordsModel,
)
from utils.log_util import logger
from utils.response_util import ResponseUtil


meeting_router = APIRouterPro(
    prefix='/system/meeting', order_num=29, tags=['系统管理 - 会议室管理'], dependencies=[PreAuthDependency()]
)


# ==================== 会议室管理接口 ====================

@meeting_router.get(
    '/room/list',
    summary='获取会议室分页列表接口',
    description='用于获取会议室分页列表',
    response_model=PageResponseModel[MeetingRoomPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:list')],
)
async def get_meeting_room_list(
    request: Request,
    page_query: Annotated[MeetingRoomPageQueryModel, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取会议室列表接口
    """
    try:
        room_list = await MeetingRoomService.get_meeting_room_list_services(db, page_query, is_page=True)
        logger.info('获取会议室列表成功')
        return ResponseUtil.success(model_content=room_list)
    except Exception as e:
        logger.error(f'获取会议室列表失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.post(
    '/room',
    summary='新增会议室接口',
    description='用于新增会议室',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:add')],
)
@Log(title='会议室管理', business_type=BusinessType.INSERT)
async def add_meeting_room(
    request: Request,
    page_object: AddMeetingRoomModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    新增会议室接口
    """
    try:
        result = await MeetingRoomService.add_meeting_room_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'新增会议室失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.put(
    '/room',
    summary='编辑会议室接口',
    description='用于编辑会议室',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:edit')],
)
@Log(title='会议室管理', business_type=BusinessType.UPDATE)
async def edit_meeting_room(
    request: Request,
    page_object: EditMeetingRoomModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    编辑会议室接口
    """
    try:
        result = await MeetingRoomService.edit_meeting_room_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'编辑会议室失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.delete(
    '/room/{id}',
    summary='删除会议室接口',
    description='用于删除会议室',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:remove')],
)
@Log(title='会议室管理', business_type=BusinessType.DELETE)
async def delete_meeting_room(
    request: Request,
    id: Annotated[int, Path(description='需要删除的会议室 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    删除会议室接口（逻辑删除）
    """
    try:
        page_object = DeleteMeetingRoomModel(id=id)
        result = await MeetingRoomService.delete_meeting_room_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'删除会议室失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.put(
    '/room/status',
    summary='更新会议室状态接口',
    description='用于更新会议室状态',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:status')],
)
@Log(title='会议室管理', business_type=BusinessType.UPDATE)
async def update_meeting_room_status(
    request: Request,
    page_object: MeetingRoomStatusModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    更新会议室状态接口
    """
    try:
        result = await MeetingRoomService.update_meeting_room_status_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'更新会议室状态失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.get(
    '/room/{id}',
    summary='获取会议室详情接口',
    description='用于获取指定会议室的详细信息',
    response_model=DataResponseModel[MeetingRoomPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:room:query')],
)
async def get_meeting_room_detail(
    request: Request,
    id: Annotated[int, Path(description='会议室 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取会议室详细信息接口
    """
    try:
        room_detail = await MeetingRoomService.meeting_room_detail_services(db, id)
        logger.info(f'获取 id 为{id}的会议室信息成功')
        return ResponseUtil.success(data=room_detail)
    except Exception as e:
        logger.error(f'获取会议室详情失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


# ==================== 会议室预定接口 ====================

@meeting_router.get(
    '/order/list',
    summary='获取预定分页列表接口',
    description='用于获取预定分页列表',
    response_model=PageResponseModel[MeetingOrderPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:order:list')],
)
async def get_meeting_order_list(
    request: Request,
    page_query: Annotated[MeetingOrderPageQueryModel, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取预定列表接口
    """
    try:
        order_list = await MeetingOrderService.get_meeting_order_list_services(db, page_query, is_page=True)
        logger.info('获取预定列表成功')
        return ResponseUtil.success(model_content=order_list)
    except Exception as e:
        logger.error(f'获取预定列表失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.post(
    '/order',
    summary='新增预定接口',
    description='用于新增预定',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:order:add')],
)
@Log(title='会议室预定', business_type=BusinessType.INSERT)
async def add_meeting_order(
    request: Request,
    page_object: AddMeetingOrderModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    新增预定接口
    """
    try:
        result = await MeetingOrderService.add_meeting_order_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'新增预定失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.put(
    '/order',
    summary='编辑预定接口',
    description='用于编辑预定',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:order:edit')],
)
@Log(title='会议室预定', business_type=BusinessType.UPDATE)
async def edit_meeting_order(
    request: Request,
    page_object: EditMeetingOrderModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    编辑预定接口
    """
    try:
        result = await MeetingOrderService.edit_meeting_order_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'编辑预定失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.delete(
    '/order/{id}',
    summary='删除预定接口',
    description='用于删除预定',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:order:remove')],
)
@Log(title='会议室预定', business_type=BusinessType.DELETE)
async def delete_meeting_order(
    request: Request,
    id: Annotated[int, Path(description='需要删除的预定 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    删除预定接口
    """
    try:
        page_object = DeleteMeetingOrderModel(id=id)
        result = await MeetingOrderService.delete_meeting_order_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'删除预定失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.get(
    '/order/{id}',
    summary='获取预定详情接口',
    description='用于获取指定预定的详细信息',
    response_model=DataResponseModel[MeetingOrderPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:order:query')],
)
async def get_meeting_order_detail(
    request: Request,
    id: Annotated[int, Path(description='预定 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取预定详细信息接口
    """
    try:
        order_detail = await MeetingOrderService.meeting_order_detail_services(db, id)
        logger.info(f'获取 id 为{id}的预定信息成功')
        return ResponseUtil.success(data=order_detail)
    except Exception as e:
        logger.error(f'获取预定详情失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


# ==================== 会议纪要接口 ====================

@meeting_router.get(
    '/records/list',
    summary='获取会议纪要分页列表接口',
    description='用于获取会议纪要分页列表',
    response_model=PageResponseModel[MeetingRecordsPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:records:list')],
)
async def get_meeting_records_list(
    request: Request,
    page_query: Annotated[MeetingRecordsPageQueryModel, Query()],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取会议纪要列表接口
    """
    try:
        records_list = await MeetingRecordsService.get_meeting_records_list_services(db, page_query, is_page=True)
        logger.info('获取会议纪要列表成功')
        return ResponseUtil.success(model_content=records_list)
    except Exception as e:
        logger.error(f'获取会议纪要列表失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.post(
    '/records',
    summary='新增会议纪要接口',
    description='用于新增会议纪要',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:records:add')],
)
@Log(title='会议纪要', business_type=BusinessType.INSERT)
async def add_meeting_records(
    request: Request,
    page_object: AddMeetingRecordsModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    新增会议纪要接口
    """
    try:
        result = await MeetingRecordsService.add_meeting_records_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'新增会议纪要失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.put(
    '/records',
    summary='编辑会议纪要接口',
    description='用于编辑会议纪要',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:records:edit')],
)
@Log(title='会议纪要', business_type=BusinessType.UPDATE)
async def edit_meeting_records(
    request: Request,
    page_object: EditMeetingRecordsModel,
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    编辑会议纪要接口
    """
    try:
        result = await MeetingRecordsService.edit_meeting_records_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'编辑会议纪要失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.delete(
    '/records/{id}',
    summary='删除会议纪要接口',
    description='用于删除会议纪要',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('system:meeting:records:remove')],
)
@Log(title='会议纪要', business_type=BusinessType.DELETE)
async def delete_meeting_records(
    request: Request,
    id: Annotated[int, Path(description='需要删除的会议纪要 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    删除会议纪要接口
    """
    try:
        page_object = DeleteMeetingRecordsModel(id=id)
        result = await MeetingRecordsService.delete_meeting_records_services(request, db, page_object)
        logger.info(result.message)
        return ResponseUtil.success(msg=result.message)
    except Exception as e:
        logger.error(f'删除会议纪要失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))


@meeting_router.get(
    '/records/{id}',
    summary='获取会议纪要详情接口',
    description='用于获取指定会议纪要的详细信息',
    response_model=DataResponseModel[MeetingRecordsPageQueryModel],
    dependencies=[UserInterfaceAuthDependency('system:meeting:records:query')],
)
async def get_meeting_records_detail(
    request: Request,
    id: Annotated[int, Path(description='会议纪要 ID')],
    db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    """
    获取会议纪要详细信息接口
    """
    try:
        records_detail = await MeetingRecordsService.meeting_records_detail_services(db, id)
        logger.info(f'获取 id 为{id}的会议纪要信息成功')
        return ResponseUtil.success(data=records_detail)
    except Exception as e:
        logger.error(f'获取会议纪要详情失败：{str(e)}')
        return ResponseUtil.error(msg=str(e))
