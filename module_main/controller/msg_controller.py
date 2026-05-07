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
from module_administrative.entity.do.message_do import OaMessage
from module_administrative.entity.do.msg_do import OaMsg
from module_administrative.entity.vo.message_vo import OaMessagePageQueryModel, OaMessageBaseModel, \
    OaMessageDeleteModel, OaMessageStarModel, OaMessageClearModel
from module_administrative.entity.vo.msg_vo import OaMsgQueryPageModel, OaMsgBaseModel
from module_administrative.service.message_service import MessageService
from utils.response_util import ResponseUtil
from module_admin.entity.vo.user_vo import (
    CurrentUserModel
)

msg_controller = APIRouterPro(
    prefix='/main/message', order_num=3, tags=['主页-消息中心'], dependencies=[PreAuthDependency()]
)
# ------------------------------------------------ 发件箱 --------------------------------------------
@msg_controller.get(
    '/send/get_list',
    summary='获取发送列表',
    description='获取发送列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:query')],
)
async def get_send_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaMessagePageQueryModel, Query()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaMessage)],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    """
    获取发送列表
    """
    model.from_uid = current_user.user.user_id
    result = await MessageService.get_list(query_db, model, data_scope_sql, True)
    return ResponseUtil.success(model_content=result)

@msg_controller.get(
    '/send/get_detail/{message_id}',
    summary='获取发送详情',
    description='获取发送详情',
    response_model=OaMessageBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:query')],
)
async def get_send_detail(
        message_id: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    """
    获取发送详情
    """
    result = await MessageService.get_send_detail(query_db, message_id)
    if not result:
        return ResponseUtil.error("未找到该记录")
    return ResponseUtil.success(data=result)

@msg_controller.put(
    '/send/update',
    summary='更新发送',
    description='更新发送',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:edit')],
)
@Log(title='编辑发送消息',business_type=BusinessType.UPDATE)
async def update_send_message(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    update_model: Annotated[OaMessageBaseModel, Body()]
)->Response:
    """
    更新发送
    """
    result = await MessageService.update(query_db, update_model)
    return ResponseUtil.success(msg=result.message)

@msg_controller.post(
    '/send/add',
    summary='新增发送',
    description='新增发送',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:add')],
)
@Log(title='新增发送消息',business_type=BusinessType.INSERT)
async def add_send_message(
    request: Request,
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    create_model: Annotated[OaMessageBaseModel, Body()]
) -> Response:
    """
    新增发送
    """
    create_model.from_uid = current_user.user.user_id
    result = await MessageService.add(query_db, create_model)
    return ResponseUtil.success(msg=result.message)
@msg_controller.delete(
    '/delete',
    summary='删除发送',
    description='删除发送',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:del')],
)
@Log(title='删除发送消息',business_type=BusinessType.DELETE)
async def delete_message(
    request: Request,
    delete_model: Annotated[OaMessageDeleteModel, Body()],
    query_db: Annotated[AsyncSession, DBSessionDependency()]
)->Response:
    """
    删除发送
    """
    result = await MessageService.delete(query_db, delete_model.message_ids, delete_model.table)
    return ResponseUtil.success(msg=result.message)

@msg_controller.put(
    '/send',
    summary='更新发送',
    description='更新发送',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:edit')],
)
@Log(title='发送消息',business_type=BusinessType.UPDATE)
async def send_update(
        request: Request,
        query_db: Annotated[AsyncSession, DBSessionDependency()],
        messageId: int,
)->Response:
    result = await MessageService.send(query_db, messageId)
    return ResponseUtil.success(msg=result.message)
# ------------------------------------------- 垃圾箱 -------------------------------------------

@msg_controller.get(
    '/get_rubbish_list',
    summary='获取回收站消息列表',
    description='获取回收站消息列表',
    response_model=None,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:query')],
)
async def get_rubbish_list(
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaMessagePageQueryModel, Query()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaMessage)],
) -> Response:
    """
    获取回收站消息列表
    """
    user_id = current_user.user.user_id
    result = await MessageService.get_rubbish_list(query_db, user_id, model, data_scope_sql, True)
    return ResponseUtil.success(model_content=result)

@msg_controller.put(
    '/restore',
    summary='还原消息',
    description='还原消息',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:restore')],
)
@Log(title='还原消息',business_type=BusinessType.UPDATE)
async def restore_message(
    request: Request,
    model: Annotated[OaMessageClearModel, Body()],
    query_db: Annotated[AsyncSession, DBSessionDependency()]
)->Response:
    """
    还原消息
    """
    result = await MessageService.restore(query_db, model.message_id, model.table)
    return ResponseUtil.success(msg=result.message)

@msg_controller.put(
    '/clear',
    summary='清空发送',
    description='清空发送',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:clear')],
)
@Log(title='清除消息',business_type=BusinessType.UPDATE)
async def clear_message(
    request: Request,
    model: Annotated[OaMessageClearModel, Body()],
    query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    """
    清除发送
    """
    result = await MessageService.clear(query_db, model.message_id, model.table)
    return ResponseUtil.success(msg=result.message)

# ___________________________________________ 收件箱 _____________________________________________



@msg_controller.get(
    '/receive/get_list',
    summary='获取收件箱消息列表',
    description='获取收件箱消息列表',
    response_model=OaMsgBaseModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:query')],
)
async def get_res_list(
query_db: Annotated[AsyncSession, DBSessionDependency()],
    model: Annotated[OaMsgQueryPageModel, Query()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    data_scope_sql: Annotated[ColumnElement, DataScopeDependency(OaMsg)],
)-> Response:
    """
    获取收件箱消息列表
    """
    model.to_uid = current_user.user.user_id
    result = await MessageService.get_receive_list(query_db, model, data_scope_sql, True)
    return ResponseUtil.success(model_content=result)

@msg_controller.put(
    '/receive/set_stars',
    summary='批量设置消息标星',
    description='批量设置消息标星',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:edit')],
)
@Log(title='批量设置消息标星',business_type=BusinessType.UPDATE)
async def set_stars(
        request: Request,
        model: Annotated[OaMessageStarModel,Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    """
    批量设置消息标星
    """
    result = await MessageService.set_star(query_db, model.message_ids, model.is_star)
    return ResponseUtil.success(msg=result.message)
@msg_controller.put(
    '/receive/set_star',
    summary='设置消息标星',
    description='设置消息标星',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:edit')],
)
@Log(title='设置消息标星',business_type=BusinessType.UPDATE)
async def set_star(
        request: Request,
        messageId: int,
        isStar: int,
        query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    """
    设置消息标星
    """
    result = await MessageService.set_star(query_db, [messageId], isStar)
    return ResponseUtil.success(msg=result.message)

@msg_controller.put(
    '/receive/set_reads',
    summary='设置消息已读',
    description='设置消息已读',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:edit')],
)
@Log(title='设置消息已读',business_type=BusinessType.UPDATE)
async def set_reads(
        request: Request,
        model: Annotated[OaMessageDeleteModel,Body()],
        query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    """
    设置消息已读
    """
    result = await MessageService.set_reads(query_db, model.message_ids)
    return ResponseUtil.success(msg=result.message)

@msg_controller.put(
    '/receive/read',
    summary='查看消息',
    description='查看消息',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:read')],
)
@Log(title='查看消息',business_type=BusinessType.UPDATE)
async def read(
    request: Request,
    messageId: int,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    """
    阅读消息
    """
    result = await MessageService.set_read(query_db, messageId)
    return ResponseUtil.success(data=result)

@msg_controller.delete(
    '/receive/deletes',
    summary='批量删除消息',
    description='批量删除消息',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:del')],
)
@Log(title='批量删除消息',business_type=BusinessType.DELETE)
async def deletes(
    request: Request,
    messageIds: list[int],
    table:str,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
):
    """
    批量删除消息
    """
    result = await MessageService.delete(query_db, messageIds, table)
    return ResponseUtil.success(msg=result.message)

@msg_controller.delete(
    '/receive/delete',
    summary='删除消息',
    description='删除消息',
    response_model=CurrentUserModel,
    dependencies=[UserInterfaceAuthDependency('oa:mian:message:del')],
)
@Log(title='删除消息',business_type=BusinessType.DELETE)
async def delete(
    request: Request,
    messageId: int,
    table:str,
    query_db: Annotated[AsyncSession, DBSessionDependency()]
) -> Response:
    """
    删除消息
    """
    result = await MessageService.delete(query_db, [messageId], table)
    return ResponseUtil.success(msg=result.message)
