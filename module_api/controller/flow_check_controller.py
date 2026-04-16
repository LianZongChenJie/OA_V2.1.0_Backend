from typing import Annotated
from datetime import datetime

from fastapi import Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from common.vo import ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_basicdata.entity.do.public.flow_do import OaFlow
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_api.entity.vo.flow_check_vo import SubmitCheckRequest, FlowCheckRequest
from module_api.service.flow_check_service import FlowCheckService
from utils.log_util import logger
from utils.response_util import ResponseUtil


flow_check_controller = APIRouterPro(
    prefix='/api/flow', order_num=1, tags=['API - 审批流程'], dependencies=[PreAuthDependency()]
)


@flow_check_controller.get(
    '/getFlows',
    summary='获取审核流程列表',
    description='根据审批类型名称获取可用的审批流程列表',
    response_model=ResponseBaseModel,
)
async def get_flows(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    check_name: str = Query(description='审批类型名称'),
):
    try:
        cate_result = await FlowCateDao.get_flow_cate_info_by_name(query_db, check_name)
        if not cate_result or cate_result.status != 1:
            return ResponseUtil.success(data=[])
        
        cate_id = cate_result.id
        
        query = (
            select(OaFlow)
            .where(
                OaFlow.cate_id == cate_id,
                OaFlow.status == 1,
                OaFlow.delete_time == 0
            )
            .order_by(OaFlow.create_time.desc())
        )
        flows = (await query_db.execute(query)).scalars().all()
        
        flow_list = []
        for flow in flows:
            flow_dict = {
                'id': flow.id,
                'cateId': flow.cate_id,
                'title': flow.title,
                'flowList': flow.flow_list,
                'copyUids': flow.copy_uids,
                'departmentIds': flow.department_ids,
                'status': flow.status,
                'createTime': flow.create_time,
                'updateTime': flow.update_time,
            }
            flow_list.append(flow_dict)
        
        logger.info(f'获取审批流程列表成功: {check_name}')
        return ResponseUtil.success(data=flow_list)
    except Exception as e:
        logger.error(f'获取审批流程列表失败: {str(e)}')
        return ResponseUtil.error(msg=str(e))


@flow_check_controller.post(
    '/submitCheck',
    summary='提交审批申请',
    description='提交审批申请，创建审批流程和记录',
    response_model=ResponseBaseModel,
)
async def submit_check(
    request: Request,
    submit_data: SubmitCheckRequest,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
):
    uid = current_user.user.user_id
    result = await FlowCheckService.submit_check(query_db, submit_data, uid)
    
    if result['success']:
        logger.info(f'提交审批申请成功: action_id={submit_data.action_id}')
        return ResponseUtil.success(msg=result['msg'])
    else:
        logger.error(f'提交审批申请失败: {result["msg"]}')
        return ResponseUtil.error(msg=result['msg'])


@flow_check_controller.post(
    '/flowCheck',
    summary='流程审核',
    description='审批通过、拒绝、撤回或反确认',
    response_model=ResponseBaseModel,
)
async def flow_check(
    request: Request,
    check_data: FlowCheckRequest,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
):
    uid = current_user.user.user_id
    result = await FlowCheckService.flow_check(query_db, check_data, uid)
    
    if result['success']:
        logger.info(f'流程审核成功: action_id={check_data.action_id}')
        return ResponseUtil.success(msg=result['msg'], data={'checkStatus': result.get('checkStatus')})
    else:
        logger.error(f'流程审核失败: {result["msg"]}')
        return ResponseUtil.error(msg=result['msg'])


@flow_check_controller.get(
    '/getFlowNodes',
    summary='获取审核流程节点',
    description='获取审批详情、审批记录和审批节点信息',
    response_model=ResponseBaseModel,
)
async def get_flow_nodes(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
    check_name: str = Query(description='审批类型名称'),
    action_id: int = Query(description='审批内容ID'),
    flow_id: int = Query(description='流程ID'),
):
    uid = current_user.user.user_id
    did = current_user.user.dept_id if current_user.user else 0
    
    result = await FlowCheckService.get_flow_nodes(query_db, check_name, action_id, flow_id, uid, did)
    
    if result['success']:
        return ResponseUtil.success(data=result['data'])
    else:
        return ResponseUtil.error(msg=result['msg'])


@flow_check_controller.get(
    '/getFlowUsers',
    summary='根据流程ID获取审批步骤和审批人',
    description='根据流程ID获取该流程的审批步骤和审批人信息',
    response_model=ResponseBaseModel,
)
async def get_flow_users(
    request: Request,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    flow_id: int = Query(description='流程ID'),
):
    result = await FlowCheckService.get_flow_users(query_db, flow_id)
    
    if result['success']:
        logger.info(f'获取流程审批人成功: flow_id={flow_id}')
        return ResponseUtil.success(data=result['data'])
    else:
        logger.error(f'获取流程审批人失败: {result["msg"]}')
        return ResponseUtil.error(msg=result['msg'])

async def _get_department_leader(query_db: AsyncSession, uid: int, level: int = 0) -> str:
    try:
        dept_query = text("SELECT did, leader_ids FROM oa_admin WHERE id = :uid")
        dept_result = await query_db.execute(dept_query, {'uid': uid})
        dept_row = dept_result.first()

        if not dept_row:
            return ''

        did = dept_row[0]
        leader_ids = dept_row[1]

        if level == 1:
            parent_dept_query = text("SELECT parent_id FROM oa_dept WHERE id = :did")
            parent_dept_result = await query_db.execute(parent_dept_query, {'did': did})
            parent_dept_row = parent_dept_result.first()

            if parent_dept_row and parent_dept_row[0]:
                parent_did = parent_dept_row[0]
                parent_leader_query = text("SELECT leader_ids FROM oa_dept WHERE id = :parent_did")
                parent_leader_result = await query_db.execute(parent_leader_query, {'parent_did': parent_did})
                parent_leader_row = parent_leader_result.first()

                if parent_leader_row and parent_leader_row[0]:
                    return parent_leader_row[0]

        return leader_ids or ''
    except Exception as e:
        logger.error(f'获取部门负责人失败: {str(e)}')
        return ''


async def _send_message(
    query_db: AsyncSession,
    from_uid: int,
    to_uids: str,
    template_id: int,
    template_field: int,
    create_time: int,
    action_id: int,
    title: str
):
    try:
        from datetime import datetime as dt
        create_time_str = dt.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S') if create_time else ''

        to_uids_list = [int(uid_item.strip()) for uid_item in to_uids.split(',') if uid_item.strip()]

        for to_uid in to_uids_list:
            await query_db.execute(
                text("""
                    INSERT INTO oa_message 
                    (from_uid, to_uid, template_id, template_field, content, create_time)
                    VALUES 
                    (:from_uid, :to_uid, :template_id, :template_field, :content, :create_time)
                """),
                {
                    'from_uid': from_uid,
                    'to_uid': to_uid,
                    'template_id': template_id,
                    'template_field': template_field,
                    'content': f'{{"create_time":"{create_time_str}","action_id":{action_id},"title":"{title}"}}',
                    'create_time': int(dt.now().timestamp())
                }
            )
    except Exception as e:
        logger.error(f'发送消息失败: {str(e)}')
