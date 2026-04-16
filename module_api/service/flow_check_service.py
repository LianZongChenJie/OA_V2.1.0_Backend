from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from module_api.dao.flow_check_dao import FlowCheckDao
from module_api.entity.vo.flow_check_vo import SubmitCheckRequest, FlowCheckRequest
from utils.log_util import logger


class FlowCheckService:
    """审批流程服务"""

    @classmethod
    async def submit_check(cls, db: AsyncSession, request: SubmitCheckRequest, 
                          uid: int) -> dict:
        """提交审批申请"""
        try:
            now_time = int(datetime.now().timestamp())
            
            flow_cate = await FlowCheckDao.get_flow_cate_by_name(db, request.check_name)
            if not flow_cate:
                return {'success': False, 'msg': '审批类型不存在'}
            
            flow = await FlowCheckDao.get_flow_by_id(db, request.flow_id)
            if not flow:
                return {'success': False, 'msg': '审批流程不存在'}
            
            flow_list_data = json.loads(flow.flow_list) if flow.flow_list else []
            check_table = flow_cate.check_table
            subject = flow_cate.title
            
            await FlowCheckDao.delete_old_steps(db, request.action_id, request.flow_id, now_time)
            await FlowCheckDao.delete_old_records(db, request.action_id, check_table, now_time)
            
            record_data = {
                'action_id': request.action_id,
                'check_table': check_table,
                'step_id': 0,
                'check_uid': uid,
                'flow_id': request.flow_id,
                'check_time': now_time,
                'check_status': 0,
                'content': '提交申请',
                'delete_time': 0
            }
            await FlowCheckDao.add_flow_record(db, record_data)
            
            if request.check_uids is None:
                steps = []
                sort_order = 0
                
                for value in flow_list_data:
                    check_role = value.get('checkRole', 0)
                    
                    if check_role == 1:
                        value['checkUids'] = await FlowCheckDao.get_department_leader(db, uid)
                        value['flowName'] = '当前部门负责人'
                        value['checkPositionId'] = 0
                    elif check_role == 2:
                        value['checkUids'] = await FlowCheckDao.get_department_leader(db, uid, level=1)
                        value['flowName'] = '上级部门负责人'
                        value['checkPositionId'] = 0
                    elif check_role == 3:
                        position_id = value.get('checkPositionId', 0)
                        if position_id:
                            value['checkUids'] = await cls._get_position_users(db, position_id)
                        value['flowName'] = value.get('flowName', '指定职位')
                    
                    if value.get('checkUids'):
                        steps.append({
                            'action_id': request.action_id,
                            'flow_id': request.flow_id,
                            'flow_name': value['flowName'],
                            'check_position_id': value.get('checkPositionId', 0),
                            'check_role': check_role,
                            'check_types': value.get('checkTypes', 1),
                            'check_uids': value['checkUids'],
                            'create_time': now_time,
                            'sort': sort_order
                        })
                        sort_order += 1
                
                if not steps:
                    await db.rollback()
                    return {'success': False, 'msg': '审批流程设置有问题，请联系HR或管理员'}
                
                for step_data in steps:
                    await FlowCheckDao.add_flow_step(db, step_data)
                
                first_step_uids = steps[0]['check_uids']
                await FlowCheckDao.update_business_table(db, check_table, request.action_id, {
                    'check_flow_id': request.flow_id,
                    'check_status': 1,
                    'check_step_sort': 0,
                    'check_uids': first_step_uids,
                    'check_copy_uids': request.check_copy_uids or ''
                })
                
                if flow_cate.template_id > 0 and first_step_uids:
                    try:
                        await cls._send_messages(db, uid, first_step_uids, flow_cate.template_id, 0, 
                                               now_time, request.action_id, subject)
                    except Exception as e:
                        logger.warning(f'发送消息通知失败: {str(e)}')
                
                await db.commit()
                return {'success': True, 'msg': '操作成功'}
            else:
                step_data = {
                    'action_id': request.action_id,
                    'flow_id': request.flow_id,
                    'flow_name': '自由审批',
                    'check_uids': request.check_uids,
                    'create_time': now_time,
                    'sort': 0
                }
                await FlowCheckDao.add_flow_step(db, step_data)
                
                await FlowCheckDao.update_business_table(db, check_table, request.action_id, {
                    'check_flow_id': request.flow_id,
                    'check_status': 1,
                    'check_step_sort': 0,
                    'check_uids': request.check_uids,
                    'check_copy_uids': request.check_copy_uids or ''
                })
                
                if flow_cate.template_id > 0 and request.check_uids:
                    try:
                        await cls._send_messages(db, uid, request.check_uids, flow_cate.template_id, 0,
                                               now_time, request.action_id, subject)
                    except Exception as e:
                        logger.warning(f'发送消息通知失败: {str(e)}')
                
                await db.commit()
                return {'success': True, 'msg': '操作成功'}
                
        except Exception as e:
            await db.rollback()
            logger.error(f'提交审批申请失败: {str(e)}')
            return {'success': False, 'msg': str(e)}

    @classmethod
    async def flow_check(cls, db: AsyncSession, request: FlowCheckRequest, 
                        uid: int) -> dict:
        """流程审核"""
        try:
            now_time = int(datetime.now().timestamp())
            
            flow_cate = await FlowCheckDao.get_flow_cate_by_name(db, request.check_name)
            if not flow_cate:
                return {'success': False, 'msg': '审批类型不存在'}
            
            check_table = flow_cate.check_table
            table_name = check_table if check_table.startswith('oa_') else f'oa_{check_table}'
            subject = flow_cate.title
            
            detail_result = await db.execute(
                text(f"SELECT * FROM `{table_name}` WHERE id = :action_id"),
                {'action_id': request.action_id}
            )
            detail_row = detail_result.first()
            
            if not detail_row:
                return {'success': False, 'msg': '审批数据错误'}
            
            detail = dict(detail_row._mapping)
            
            step = await FlowCheckDao.get_current_step(
                db, request.action_id, detail['check_flow_id'], detail['check_step_sort']
            )
            
            if not step:
                return {'success': False, 'msg': '当前审核节点不存在'}
            
            if request.check == 1:
                return await cls._approve_pass(db, detail, step, request, uid, now_time, flow_cate, subject, table_name)
            elif request.check == 2:
                return await cls._approve_reject(db, detail, step, request, uid, now_time, flow_cate, subject, table_name)
            elif request.check == 3:
                return await cls._approve_withdraw(db, detail, step, request, uid, now_time, table_name)
            elif request.check == 4:
                return await cls._approve_reverse(db, detail, step, request, uid, now_time, table_name)
            else:
                return {'success': False, 'msg': '无效的审核操作'}
                
        except Exception as e:
            await db.rollback()
            logger.error(f'流程审核失败: {str(e)}')
            return {'success': False, 'msg': str(e)}

    @classmethod
    async def _approve_pass(cls, db, detail, step, request, uid, now_time, flow_cate, subject, check_table):
        """审批通过"""
        check_uids_list = detail['check_uids'].split(',') if detail['check_uids'] else []
        if str(uid) not in check_uids_list:
            return {'success': False, 'msg': '您没权限审核该审批'}
        
        param = {
            'check_status': 1,
            'check_uids': detail['check_uids'],
            'check_step_sort': detail['check_step_sort']
        }
        
        if step['check_role'] == 0:
            if request.check_node == 2:
                next_step = detail['check_step_sort'] + 1
                
                await FlowCheckDao.add_flow_step(db, {
                    'action_id': request.action_id,
                    'sort': next_step,
                    'flow_id': detail['check_flow_id'],
                    'check_uids': request.check_uids or '',
                    'create_time': now_time
                })
                
                param['check_step_sort'] = next_step
            else:
                param['check_status'] = 2
                param['check_uids'] = ''
        else:
            check_count_result = await db.execute(
                text("""
                    SELECT COUNT(*) FROM oa_flow_record 
                    WHERE action_id = :action_id 
                      AND flow_id = :flow_id 
                      AND step_id = :step_id
                """),
                {
                    'action_id': request.action_id,
                    'flow_id': detail['check_flow_id'],
                    'step_id': step['id']
                }
            )
            check_count = check_count_result.scalar()
            
            flow_count = len(step['check_uids'].split(',')) if step['check_uids'] else 0
            
            uids_array = detail['check_uids'].split(',') if detail['check_uids'] else []
            new_uids = [u for u in uids_array if u != str(uid)]
            param['check_uids'] = ','.join(new_uids)
            
            if ((check_count + 1) >= flow_count and step['check_types'] == 1) or step['check_types'] == 2:
                next_step = await FlowCheckDao.get_current_step(
                    db, request.action_id, detail['check_flow_id'], detail['check_step_sort'] + 1
                )
                
                if next_step:
                    if next_step['check_role'] == 1:
                        param['check_uids'] = await FlowCheckDao.get_department_leader(db, detail['admin_id'])
                    elif next_step['check_role'] == 2:
                        param['check_uids'] = await FlowCheckDao.get_department_leader(db, detail['admin_id'], level=1)
                    elif next_step['check_role'] == 3:
                        param['check_uids'] = await cls._get_position_users(db, next_step['check_position_id'])
                    else:
                        param['check_uids'] = next_step['check_uids']
                    
                    param['check_step_sort'] = detail['check_step_sort'] + 1
                else:
                    param['check_status'] = 2
                    param['check_uids'] = ''
        
        if param['check_status'] == 1 and not param['check_uids']:
            return {'success': False, 'msg': '找不到下一步的审批人'}
        
        if not detail.get('check_history_uids'):
            param['check_history_uids'] = str(uid)
        else:
            param['check_history_uids'] = f"{detail['check_history_uids']},{uid}"
        
        await FlowCheckDao.update_business_table(db, check_table, request.action_id, param)
        
        await FlowCheckDao.add_flow_record(db, {
            'action_id': request.action_id,
            'check_table': check_table,
            'step_id': step['id'],
            'check_uid': uid,
            'flow_id': detail['check_flow_id'],
            'check_time': now_time,
            'check_files': request.check_files or '',
            'check_status': request.check,
            'content': request.content,
            'delete_time': 0
        })
        
        if param['check_status'] == 1 and flow_cate.template_id > 0 and param['check_uids']:
            try:
                await cls._send_messages(
                    db, detail['admin_id'], param['check_uids'], 
                    flow_cate.template_id, 0, detail.get('create_time', now_time),
                    request.action_id, subject
                )
            except Exception as e:
                logger.warning(f'发送消息失败: {str(e)}')
        
        if param['check_status'] == 2 and flow_cate.template_id > 0:
            try:
                await cls._send_messages(
                    db, uid, str(detail['admin_id']),
                    flow_cate.template_id, 1, detail.get('create_time', now_time),
                    request.action_id, subject
                )
                
                if detail.get('check_copy_uids'):
                    await cls._send_messages(
                        db, detail['admin_id'], detail['check_copy_uids'],
                        flow_cate.template_id, 3, detail.get('create_time', now_time),
                        request.action_id, subject
                    )
            except Exception as e:
                logger.warning(f'发送消息失败: {str(e)}')
        
        await db.commit()
        return {'success': True, 'msg': '操作成功', 'checkStatus': param['check_status']}

    @classmethod
    async def _approve_reject(cls, db, detail, step, request, uid, now_time, flow_cate, subject, check_table):
        """审批拒绝"""
        check_uids_list = detail['check_uids'].split(',') if detail['check_uids'] else []
        if str(uid) not in check_uids_list:
            return {'success': False, 'msg': '您没权限审核该审批'}
        
        param = {
            'check_status': 3,
            'check_uids': '',
            'check_step_sort': detail['check_step_sort']
        }
        
        if not detail.get('check_history_uids'):
            param['check_history_uids'] = str(uid)
        else:
            param['check_history_uids'] = f"{detail['check_history_uids']},{uid}"
        
        if step['check_role'] == 5:
            prev_step = await FlowCheckDao.get_current_step(
                db, request.action_id, detail['check_flow_id'], detail['check_step_sort'] - 1
            )
            
            if prev_step:
                param['check_step_sort'] = prev_step['sort']
                param['check_uids'] = prev_step['check_uids']
                param['check_status'] = 1
            else:
                param['check_step_sort'] = 0
                param['check_uids'] = ''
                param['check_status'] = 0
        
        await FlowCheckDao.update_business_table(db, check_table, request.action_id, param)
        
        await FlowCheckDao.add_flow_record(db, {
            'action_id': request.action_id,
            'check_table': check_table,
            'step_id': step['id'],
            'check_uid': uid,
            'flow_id': detail['check_flow_id'],
            'check_time': now_time,
            'check_files': request.check_files or '',
            'check_status': request.check,
            'content': request.content,
            'delete_time': 0
        })
        
        if flow_cate.template_id > 0:
            try:
                await cls._send_messages(
                    db, uid, str(detail['admin_id']),
                    flow_cate.template_id, 2, detail.get('create_time', now_time),
                    detail['id'], subject
                )
            except Exception as e:
                logger.warning(f'发送消息失败: {str(e)}')
        
        await db.commit()
        return {'success': True, 'msg': '操作成功', 'checkStatus': param['check_status']}

    @classmethod
    async def _approve_withdraw(cls, db, detail, step, request, uid, now_time, check_table):
        """审批撤回"""
        if detail['admin_id'] != uid:
            return {'success': False, 'msg': '你没权限操作'}
        
        param = {
            'check_status': 4,
            'check_uids': '',
            'check_step_sort': 0
        }
        
        await FlowCheckDao.update_business_table(db, check_table, request.action_id, param)
        
        await FlowCheckDao.add_flow_record(db, {
            'action_id': request.action_id,
            'check_table': check_table,
            'step_id': step['id'],
            'check_uid': uid,
            'flow_id': detail['check_flow_id'],
            'check_time': now_time,
            'check_status': request.check,
            'content': request.content,
            'delete_time': 0
        })
        
        await db.commit()
        return {'success': True, 'msg': '操作成功', 'checkStatus': param['check_status']}

    @classmethod
    async def _approve_reverse(cls, db, detail, step, request, uid, now_time, check_table):
        """审批反确认"""
        param = {
            'check_status': 0,
            'check_uids': '',
            'check_step_sort': 0
        }
        
        await FlowCheckDao.update_business_table(db, check_table, request.action_id, param)
        
        await FlowCheckDao.add_flow_record(db, {
            'action_id': request.action_id,
            'check_table': check_table,
            'step_id': step['id'],
            'check_uid': uid,
            'flow_id': detail['check_flow_id'],
            'check_time': now_time,
            'check_status': 4,
            'content': request.content,
            'delete_time': 0
        })
        
        await db.commit()
        return {'success': True, 'msg': '操作成功', 'checkStatus': 0}

    @classmethod
    async def _get_position_users(cls, db: AsyncSession, position_id: int) -> str:
        """获取指定职位的用户IDs"""
        result = await db.execute(
            text("SELECT id FROM oa_admin WHERE position_id = :position_id AND status = 1"),
            {'position_id': position_id}
        )
        uids = [str(row[0]) for row in result.all()]
        return ','.join(uids)

    @classmethod
    async def _send_messages(cls, db: AsyncSession, from_uid: int, to_uids: str,
                            template_id: int, template_field: int, create_time: int,
                            action_id: int, title: str):
        """发送消息通知"""
        content_dict = {
            'create_time': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S'),
            'action_id': action_id,
            'title': title
        }
        content = json.dumps(content_dict, ensure_ascii=False)
        
        send_time = int(datetime.now().timestamp())
        
        await FlowCheckDao.send_message(
            db, from_uid, to_uids, str(template_id), action_id, content, send_time
        )

    @classmethod
    async def get_flow_nodes(cls, db: AsyncSession, check_name: str, action_id: int, 
                            flow_id: int, uid: int, did: int) -> dict:
        """获取审批流程节点"""
        try:
            from sqlalchemy import select
            from module_basicdata.entity.do.public.flow_do import OaFlow
            
            flow_cate = await FlowCheckDao.get_flow_cate_by_name(db, check_name)
            if not flow_cate:
                return {'success': False, 'msg': '审批类型不存在'}
            
            if action_id == 0:
                query = (
                    select(OaFlow)
                    .where(
                        OaFlow.cate_id == flow_cate.id,
                        OaFlow.status == 1,
                        OaFlow.delete_time == 0
                    )
                    .order_by(OaFlow.sort.desc())
                )
                flows = (await db.execute(query)).scalars().all()
                
                flow_list = []
                for flow in flows:
                    flow_dict = {
                        'id': flow.id,
                        'title': flow.title,
                        'cateId': flow.cate_id,
                        'checkType': flow.check_type,
                        'departmentIds': flow.department_ids,
                        'copyUids': flow.copy_uids,
                        'flowList': flow.flow_list,
                        'status': flow.status,
                        'remark': flow.remark,
                        'isCopy': flow_cate.is_copy
                    }
                    flow_list.append(flow_dict)
                
                return {'success': True, 'data': flow_list}
            
            check_table = flow_cate.check_table
            table_name = check_table if check_table.startswith('oa_') else f'oa_{check_table}'
            
            detail_result = await db.execute(
                text(f"""
                    SELECT id, admin_id, check_status, check_flow_id, check_step_sort, 
                           check_uids, check_copy_uids, create_time
                    FROM `{table_name}`
                    WHERE id = :action_id
                """),
                {'action_id': action_id}
            )
            detail_row = detail_result.first()
            
            if not detail_row:
                return {'success': False, 'msg': '审批数据不存在'}
            
            detail = {
                'id': detail_row[0],
                'adminId': detail_row[1],
                'checkStatus': detail_row[2],
                'checkFlowId': detail_row[3],
                'checkStepSort': detail_row[4],
                'checkUids': detail_row[5] or '',
                'checkCopyUids': detail_row[6] or '',
                'createTime': detail_row[7]
            }
            
            is_creater = 1 if detail['adminId'] == uid else 0
            detail['isCreater'] = is_creater
            
            admin_result = await db.execute(
                text("SELECT name FROM oa_admin WHERE id = :admin_id"),
                {'admin_id': detail['adminId']}
            )
            admin_row = admin_result.first()
            detail['adminName'] = admin_row[0] if admin_row else ''
            
            check_uids_list = detail['checkUids'].split(',') if detail['checkUids'] else []
            is_checker = 1 if str(uid) in check_uids_list else 0
            detail['isChecker'] = is_checker
            
            detail['isCopy'] = flow_cate.is_copy
            detail['isFile'] = flow_cate.is_file
            detail['isExport'] = flow_cate.is_export
            detail['isBack'] = flow_cate.is_back
            detail['isReversed'] = flow_cate.is_reversed
            
            records_result = await db.execute(
                text("""
                    SELECT * FROM oa_flow_record 
                    WHERE action_id = :action_id 
                      AND flow_id = :flow_id 
                      AND delete_time = 0
                    ORDER BY check_time DESC
                """),
                {'action_id': action_id, 'flow_id': detail['checkFlowId']}
            )
            records_rows = records_result.fetchall()
            
            check_record_list = []
            for record_row in records_rows:
                record = dict(record_row._mapping)
                
                name_result = await db.execute(
                    text("SELECT name FROM oa_admin WHERE id = :check_uid"),
                    {'check_uid': record['check_uid']}
                )
                name_row = name_result.first()
                record['name'] = name_row[0] if name_row else ''
                
                record['checkTimeStr'] = datetime.fromtimestamp(record['check_time']).strftime('%Y-%m-%d %H:%M') if record['check_time'] else ''
                
                status_map = {0: '提交', 1: '审核通过', 2: '审核拒绝', 3: '撤销', 4: '反确认'}
                record['statusStr'] = status_map.get(record['check_status'], '未知')
                
                if record['check_files']:
                    file_ids = [int(fid.strip()) for fid in record['check_files'].split(',') if fid.strip()]
                    if file_ids:
                        files_result = await db.execute(
                            text("SELECT * FROM oa_file WHERE id IN :file_ids"),
                            {'file_ids': tuple(file_ids)}
                        )
                        record['fileArray'] = [dict(row._mapping) for row in files_result.all()]
                    else:
                        record['fileArray'] = []
                else:
                    record['fileArray'] = []
                
                check_record_list.append(record)
            
            detail['checkRecord'] = check_record_list
            
            if detail['checkStatus'] in [0, 4]:
                query = (
                    select(OaFlow)
                    .where(
                        OaFlow.cate_id == flow_cate.id,
                        OaFlow.status == 1,
                        OaFlow.delete_time == 0
                    )
                    .order_by(OaFlow.sort.desc())
                )
                flows = (await db.execute(query)).scalars().all()
                detail['flow'] = [
                    {
                        'id': flow.id,
                        'title': flow.title,
                        'flowList': flow.flow_list,
                        'isCopy': flow_cate.is_copy
                    }
                    for flow in flows
                ]
            else:
                if detail['checkUids']:
                    uids_list = [int(uid_item.strip()) for uid_item in detail['checkUids'].split(',') if uid_item.strip()]
                    if uids_list:
                        unames_result = await db.execute(
                            text("SELECT name FROM oa_admin WHERE id IN :uids"),
                            {'uids': tuple(uids_list)}
                        )
                        detail['checkUnames'] = ','.join([row[0] for row in unames_result.all()])
                    else:
                        detail['checkUnames'] = '-'
                else:
                    detail['checkUnames'] = '-'
                
                if detail['checkCopyUids']:
                    copy_uids_list = [int(uid_item.strip()) for uid_item in detail['checkCopyUids'].split(',') if uid_item.strip()]
                    if copy_uids_list:
                        copy_unames_result = await db.execute(
                            text("SELECT name FROM oa_admin WHERE id IN :uids"),
                            {'uids': tuple(copy_uids_list)}
                        )
                        detail['copyUnames'] = ','.join([row[0] for row in copy_unames_result.all()])
                    else:
                        detail['copyUnames'] = '-'
                else:
                    detail['copyUnames'] = '-'
                
                nodes_result = await db.execute(
                    text("""
                        SELECT * FROM oa_flow_step 
                        WHERE action_id = :action_id 
                          AND flow_id = :flow_id 
                          AND delete_time = 0
                        ORDER BY sort ASC
                    """),
                    {'action_id': action_id, 'flow_id': flow_id}
                )
                nodes_rows = nodes_result.fetchall()
                
                nodes = []
                for node_row in nodes_rows:
                    node = dict(node_row._mapping)
                    
                    if node.get('check_uids'):
                        uids_list = [int(uid_item.strip()) for uid_item in node['check_uids'].split(',') if uid_item.strip()]
                        if uids_list:
                            users_result = await db.execute(
                                text("SELECT id, name, thumb FROM oa_admin WHERE id IN :uids"),
                                {'uids': tuple(uids_list)}
                            )
                            check_uids_info = [
                                {
                                    'id': row[0],
                                    'name': row[1],
                                    'thumb': row[2],
                                    'checkTime': 0,
                                    'content': '',
                                    'checkStatus': 0
                                }
                                for row in users_result.all()
                            ]
                            
                            for user_info in check_uids_info:
                                record_query_result = await db.execute(
                                    text("""
                                        SELECT check_time, content, check_status 
                                        FROM oa_flow_record 
                                        WHERE check_uid = :check_uid 
                                          AND step_id = :step_id
                                        ORDER BY check_time DESC
                                        LIMIT 1
                                    """),
                                    {'check_uid': user_info['id'], 'step_id': node['id']}
                                )
                                record_row = record_query_result.first()
                                
                                if record_row:
                                    user_info['checkTime'] = datetime.fromtimestamp(record_row[0]).strftime('%Y-%m-%d %H:%M') if record_row[0] else 0
                                    user_info['content'] = record_row[1]
                                    user_info['checkStatus'] = record_row[2]
                            
                            node['checkUidsInfo'] = check_uids_info
                        else:
                            node['checkUidsInfo'] = []
                    else:
                        node['checkUidsInfo'] = []
                    
                    if node.get('check_position_id'):
                        position_result = await db.execute(
                            text("SELECT title FROM oa_position WHERE id = :position_id"),
                            {'position_id': node['check_position_id']}
                        )
                        position_row = position_result.first()
                        node['checkPosition'] = position_row[0] if position_row else ''
                    else:
                        node['checkPosition'] = ''
                    
                    check_list = [r for r in check_record_list if r['step_id'] == node['id']]
                    node['checkList'] = check_list
                    
                    nodes.append(node)
                
                detail['nodes'] = nodes
                
                step = await FlowCheckDao.get_current_step(db, action_id, flow_id, detail['checkStepSort'])
                detail['step'] = step
            
            return {'success': True, 'data': detail}
            
        except Exception as e:
            logger.error(f'获取审批流程节点失败: {str(e)}')
            return {'success': False, 'msg': str(e)}

    @classmethod
    async def get_flow_users(cls, db: AsyncSession, flow_id: int):
        """
        根据流程ID获取审批步骤和审批人信息
        
        :param db: 数据库会话
        :param flow_id: 流程ID
        :return: 审批步骤和审批人信息
        """
        try:
            from sqlalchemy import select
            from module_basicdata.entity.do.public.flow_do import OaFlow
            
            flow_result = await db.execute(
                select(OaFlow).where(
                    OaFlow.id == flow_id,
                    OaFlow.status == 1,
                    OaFlow.delete_time == 0
                )
            )
            flow = flow_result.scalars().first()
            
            if not flow:
                return {'success': False, 'msg': '流程不存在或已禁用'}
            
            if not flow.flow_list:
                return {'success': True, 'data': []}
            
            import json
            flow_list = json.loads(flow.flow_list) if isinstance(flow.flow_list, str) else flow.flow_list
            
            result_steps = []
            
            for step_index, step_config in enumerate(flow_list):
                check_role = step_config.get('checkRole', 0)
                check_uids_str = ''
                user_list = []
                
                if check_role == 0:
                    check_uids_str = step_config.get('checkUids', '')
                    if check_uids_str:
                        uids_list = [int(uid.strip()) for uid in check_uids_str.split(',') if uid.strip()]
                        if uids_list:
                            users_result = await db.execute(
                                text("SELECT id, name, thumb FROM oa_admin WHERE id IN :uids AND status = 1"),
                                {'uids': tuple(uids_list)}
                            )
                            user_list = [
                                {
                                    'id': row[0],
                                    'name': row[1],
                                    'thumb': row[2]
                                }
                                for row in users_result.all()
                            ]
                
                elif check_role == 1:
                    user_list = [{'id': 0, 'name': '当前部门负责人', 'thumb': ''}]
                    check_uids_str = 'dynamic_leader'
                
                elif check_role == 2:
                    user_list = [{'id': 0, 'name': '上一级部门负责人', 'thumb': ''}]
                    check_uids_str = 'dynamic_parent_leader'
                
                elif check_role == 3:
                    position_id = step_config.get('checkPositionId', 0)
                    if position_id:
                        position_result = await db.execute(
                            text("SELECT title FROM oa_position WHERE id = :position_id"),
                            {'position_id': position_id}
                        )
                        position_row = position_result.first()
                        position_name = position_row[0] if position_row else ''
                        
                        position_users_result = await db.execute(
                            text("SELECT id, name, thumb FROM oa_admin WHERE position_id = :position_id AND status = 1"),
                            {'position_id': position_id}
                        )
                        user_list = [
                            {
                                'id': row[0],
                                'name': row[1],
                                'thumb': row[2]
                            }
                            for row in position_users_result.all()
                        ]
                        
                        if not user_list:
                            user_list = [{'id': 0, 'name': f'{position_name}(暂无人员)', 'thumb': ''}]
                    else:
                        user_list = [{'id': 0, 'name': '指定职位(未配置)', 'thumb': ''}]
                
                elif check_role == 4:
                    check_uids_str = step_config.get('checkUids', '')
                    if check_uids_str:
                        uids_list = [int(uid.strip()) for uid in check_uids_str.split(',') if uid.strip()]
                        if uids_list:
                            users_result = await db.execute(
                                text("SELECT id, name, thumb FROM oa_admin WHERE id IN :uids AND status = 1"),
                                {'uids': tuple(uids_list)}
                            )
                            user_list = [
                                {
                                    'id': row[0],
                                    'name': row[1],
                                    'thumb': row[2]
                                }
                                for row in users_result.all()
                            ]
                
                elif check_role == 5:
                    user_list = [{'id': 0, 'name': '可回退审批', 'thumb': ''}]
                    check_uids_str = 'reversible'
                
                role_name_map = {
                    0: '自由指定',
                    1: '当前部门负责人',
                    2: '上一级部门负责人',
                    3: '指定职位',
                    4: '指定用户',
                    5: '可回退审批'
                }
                
                step_info = {
                    'sort': step_index + 1,
                    'flowName': step_config.get('flowName', role_name_map.get(check_role, '未知')),
                    'checkRole': check_role,
                    'checkRoleName': role_name_map.get(check_role, '未知'),
                    'checkTypes': step_config.get('checkTypes', 1),
                    'checkTypesName': '会签' if step_config.get('checkTypes', 1) == 1 else '或签',
                    'checkPositionId': step_config.get('checkPositionId', 0),
                    'checkUids': check_uids_str,
                    'users': user_list
                }
                
                result_steps.append(step_info)
            
            return {'success': True, 'data': result_steps}
            
        except Exception as e:
            logger.error(f'获取流程审批人失败: {str(e)}')
            return {'success': False, 'msg': str(e)}
