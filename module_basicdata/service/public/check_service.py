import json

from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.dao.dept_dao import DeptDao
from module_admin.dao.post_dao import PostDao
from module_admin.dao.user_dao import UserDao
from module_basicdata.dao.public.check_dao import CheckDao
from module_basicdata.dao.public.flow_cate_dao import FlowCateDao
from module_basicdata.dao.public.flow_dao import OaFlowDao
from module_basicdata.dao.public.flow_step_dao import OaFlowStepDao
from module_basicdata.entity.do.public.flow_step_do import OaFlowStep
from module_basicdata.entity.vo.public.flow_step_vo import OaFlowStepBaseModel
from module_basicdata.entity.vo.public.flow_vo import OaFlowCheckBaseModel
from common.vo import CrudResponseModel
from datetime import datetime

from module_personnel.dao.file_dao import FileDAO
from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_personnel.entity.vo.flow_record_vo import OaFlowRecordBaseModel
from utils.camel_converter import ModelConverter
from utils.timeformat import format_timestamp


class CheckService:

    @classmethod
    async def update_table_check(cls, db: AsyncSession, check_table: str, action_id: int, check_step_sort: int,
                                 check_uids: str, check_status: int, check_history_uids: str):
        update_dict = {
            "check_step_sort": check_step_sort,
            "check_status": check_status,
            "check_history_uids": check_history_uids,
            "check_uids": check_uids,
            "action_id": action_id
        }
        sql = 'update %s set check_step_sort = :check_step_sort,check_status=:check_status,check_history_uids=:check_history_uids,check_uids=:check_uids where id = :action_id' % ('oa_'+ check_table)
        # 更新表审核信息
        result = await CheckDao.execute_update_sql(db, sql, update_dict)
        return result

    @classmethod
    async def get_check_table_detail(cls, db: AsyncSession, check_table: str, action_id : int) -> dict:
        """
        获取审核表详情
        """
        sql = 'select * from %s where id=:id' % ('oa_'+ check_table)
        result = await CheckDao.execute_row_sql(db, sql, {'id':action_id})
        return result

    @classmethod
    async def flow_check(cls, db: AsyncSession, query_model: OaFlowCheckBaseModel, user_id: int):
        """
        审核
        :param db:
        :param query_model:
        :param user_id:
        :return:
        """
        check_files = query_model.check_files
        flow = await OaFlowDao.get_flow_detail(db, query_model.flow_id)
        flow_cate = await FlowCateDao.get_flow_cate_info(db, flow.cate_id)
        subject = flow_cate.title
        action_id = query_model.action_id
        check_table = flow_cate.check_table
        check_step_sort = 0
        check_uids = None
        step = 0
        check_status = 0

        # 审核内容详情
        sql = 'select * from %s where id = :id' % ('oa_'+ check_table)
        detail = await CheckDao.execute_row_sql(db, sql, {'id':action_id})
        if not detail:
            return CrudResponseModel(is_success=False, message='审核内容详情为空')

        # 当前节点审核详情
        step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'])
        step_id = step.id
        if not step:
            return CrudResponseModel(is_success=True, message='审核已结束')

        if query_model.check_status == 1:
            if str(user_id) not in detail['check_uids'].split(','):
                return CrudResponseModel(is_success=False, message='您没有权限进行此项操作')
            # 审核通过
            if step.check_role == 0:
                # 自由人审批
                if query_model.check_node == 2:
                    next_step = detail['check_step'] + 1
                    new_step = OaFlowStep(
                        action_id=action_id,
                        sort = next_step,
                        flow_id = detail['check_flow_id'],
                        check_uid = user_id,
                        create_time = datetime.now().timestamp()
                    )
                    # 更新当前节点审核人
                    await OaFlowStepDao.add(db, new_step)
                    # 下一步审核步骤
                    step = new_step
                    check_status = 1
                else:
                    check_status = 2
                    check_uids = ''
                    check_step_sort = detail['check_step_sort'] + 1
            else:
                # 查询当前步骤审批记录
                check_count = await FlowRecordDao.get_count_by_action_id_flow_id_step_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'])
                flow_count = step.check_uids.split(',').__len__()
                check_status = 1
                check_uids = detail['check_uids'] + ',' + str(user_id)

                if ((check_count + 1) <= flow_count and step.check_types ==1) or step.check_types == 2:
                    # 会签
                    next_step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'] + 1)
                    if next_step:
                        # 存在下一步审核
                        if next_step.check_role == 1:
                            check_uids = await DeptDao.get_dept_manages(detail['admin_id'])
                        elif next_step.check_role == 2:
                            check_uids = await DeptDao.get_dept_manages(detail['admin_id'], True)
                        elif next_step.check_role == 3:
                            uids = await UserDao.get_user_by_post_id(db,next_step.check_position_id)
                            check_uids = ','.join(str(uid) for uid in uids)
                        else:
                            check_uids = next_step.check_uids
                        check_step_sort = detail['check_step_sort'] + 1
                        check_status = 1
                    else:
                        check_status = 2
                        check_step_sort = detail['check_step_sort'] + 1
                        check_uids = ''

            if check_status == 1 and check_uids is None:
                return CrudResponseModel(is_success = False, message="找不到下一步的审批人，该审批流程设置有问题，请联系HR或者管理员")
            # 添加历史审核人
            if detail['check_history_uids'] is None:
                check_history_uids = user_id
            else:
                check_history_uids = detail['check_history_uids'] + ',' + str(user_id)
            # 更新审核状态
            result = await cls.update_table_check(db, check_table, action_id, check_step_sort,check_uids, check_status, check_history_uids)
            if result:
                record= OaFlowRecordBaseModel()
                record.action_id = action_id,
                record.check_table = check_table,
                record.step_id = step_id,
                record.check_uid = user_id,
                record.flow_id = detail['check_flow_id'],
                record.check_time = datetime.now().timestamp(),
                record.check_files = query_model.check_files,
                record.check_status = check_status,
                record.content = query_model.content
                record.check_files = query_model.check_files if query_model.check_files is not None else ''
                # 添加审批记录
                await FlowRecordDao.add(db, record)

                # 添加审核日志
                # todo

                # 发送系统消息
                # todo
                return CrudResponseModel(is_success=True, data={'subject':subject, 'step':step}, message='审核成功')
            else:
                return CrudResponseModel(is_success=False, message='审核失败')
        # 审核拒绝
        elif query_model.check_status==2:
            check_uids = detail['check_uids'].split(',')
            if str(user_id) not in check_uids:
                return CrudResponseModel(is_success=False, message="您没有权限审核此审批")
            # 审核拒绝数据库操作
            check_status = 3

            # 添加历史审核人
            if not detail['check_history_uids']:
                check_history_uids = user_id
            else:
                check_history_uids = detail['check_history_uids']+ ','+ str(user_id)
            check_uids = ''

            # 可回退审核退回操作
            if step.check_role == 5:
                prev_step = await OaFlowStepDao.get_step_by_action_id_flow_id_sort(db, action_id, detail['check_flow_id'], (detail['check_step_sort']-1))
                if prev_step:
                    check_step_sort = prev_step.sort
                    check_uids = prev_step.check_uids
                    check_status = 1
                else:
                    check_step_sort = 0
                    check_uids = ''
                    check_status = 0

            # 更新审核状态
            result = await cls.update_table_check(db, check_table, action_id, check_step_sort, check_uids,
                                                  check_status, check_history_uids)
            if result:
                record = OaFlowRecordBaseModel()
                record.action_id = action_id,
                record.check_table = check_table,
                record.step_id = step_id,
                record.check_uid = user_id,
                record.flow_id = detail['check_flow_id'],
                record.check_time = datetime.now().timestamp(),
                record.check_files = query_model.check_files,
                record.check_status = check_status,
                record.content = query_model.content
                record.check_files = query_model.check_files if query_model.check_files is not None else ''
                # 添加审批记录
                await FlowRecordDao.add(db, record)
                # if flow_cate.template_id > 0:
                #
                #     pass
                # 发送消息
                # todo
                # 记录操作日志
                # todo
                return CrudResponseModel(is_success=True, message='操作成功！')
            else:
                return CrudResponseModel(is_success=False, message='操作失败！')

        # 撤回审核
        elif query_model.check_status==3:
            if detail['admin_id'] != user_id:
                return CrudResponseModel(is_success=False, message='您没有权限撤回此审批')
            # 审核撤回数据库操作
            check_status = 4
            check_uids = ''
            check_step_sort = 0
            check_history_uids = ''
            result = await cls.update_table_check(db, check_table, action_id, check_step_sort, check_uids,
                                                  check_status, check_history_uids)

            if result:
                record = OaFlowRecordBaseModel()
                record.action_id = action_id,
                record.check_table = check_table,
                record.step_id = step_id,
                record.check_uid = user_id,
                record.flow_id = detail['check_flow_id'],
                record.check_time = datetime.now().timestamp(),
                record.check_files = query_model.check_files if query_model.check_files is not None else '',
                record.check_status = check_status,
                record.content = query_model.content
                # 添加审批记录
                await FlowRecordDao.add(db, record)
                # 添加日志记录
                # todo
                return CrudResponseModel(is_success=True, message='操作成功！')
            else:
                return CrudResponseModel(is_success=False, message='操作失败！')
        # 审核反确认，数据会带待提交状态
        elif query_model.check_status==4:
            check_status = 0
            check_uids = ''
            check_step_sort = 0
            check_history_uids = ''
            result = await cls.update_table_check(db, check_table, action_id, check_step_sort, check_uids,
                                                  check_status, check_history_uids)
            if result:
                record = OaFlowRecordBaseModel()
                record.action_id = action_id
                record.check_table = check_table
                record.step_id = step_id
                record.check_uid = user_id
                record.flow_id = detail['check_flow_id']
                record.check_time = int(datetime.now().timestamp())
                record.check_files = query_model.check_files if query_model.check_files is not None else ''
                record.check_status = check_status
                record.content = query_model.content
                await FlowRecordDao.add(db, record)
                # 添加日志记录
                # todo
                return CrudResponseModel(is_success=True, message='操作成功！')
            else:
                return CrudResponseModel(is_success=False, message='操作失败！')

    @classmethod
    async def get_flow(cls, db: AsyncSession, check_name: str):
        """
        获取审核流程
        :param db:
        :param check_name:
        :return:
        """
        cate = await FlowCateDao.get_flow_cate_info_by_name(db, check_name)
        flow = await OaFlowDao.get_flow_info_by_cate_id(db, cate.id)
        return flow

    @classmethod
    async def get_flow_user(cls, db: AsyncSession, flow_id: int, user_id: int):
        """
        获取审核步骤人员
        :param db:
        :param user_id
        :param flow_id:
        :return:
        """
        data = {}
        flow = await OaFlowDao.get_flow_detail(db, flow_id)
        flow_list = []
        if flow:
            if flow.flow_list:
                step_list = json.loads(flow.flow_list)
                for flow_step in step_list:
                    flow_step['check_position']= ''
                    if flow_step['check_role'] == '1':
                        flow_step['check_uids'] = await DeptDao.get_dept_manages(db, user_id)
                    if flow_step['check_role'] == '2':
                        flow_step['check_uids'] = await DeptDao.get_dept_manages(db, user_id, True)
                    if flow_step['check_role'] == '3':
                        flow_step['check_position'] = (await PostDao.get_post_by_id(db, flow_step['check_position_id'])).post_name
                        flow_step['check_uids'] = await UserDao.get_user_by_post_id(db, flow_step['check_position_id'])
                        if flow_step['check_uids']:
                            flow_step['check_uids'] = ','.join(str(uid) for uid in flow_step['check_uids'])
                    flow_step['check_user_names'] = await UserDao.get_user_name_by_user_id(db, flow_step['check_uids'].split(','))
                    flow_list.append(flow_step)
        else:
            return []
        # 抄送人信息
        data['copy_uids'] = flow.copy_uids
        data['copy_user_names'] = await UserDao.get_user_name_by_user_id(db, flow.copy_uids.split(','))
        data['flow_list'] = flow_list
        return ModelConverter.convert_to_camel_case(data)

    @classmethod
    async def submit_check(cls, db: AsyncSession, query_model: OaFlowCheckBaseModel, user_id: int):
        """
        提交审核
        :param db: 
        :param query_model: 
        :param user_id: 
        :return: 
        """
        flow = await OaFlowDao.get_flow_detail(db, query_model.flow_id)
        flow_cate = await FlowCateDao.get_flow_cate_info(db, flow.cate_id)
        flow_data = await OaFlowDao.get_flow_info_by_cate_id(db, flow_cate.id)
        flow_cate = flow_cate.to_dict()
        flow_data = flow_data.to_dict()

        # 删除原来地审核流程和记录
        await OaFlowStepDao.delete_flow_step(db, flow_data['id'], query_model.action_id)
        await FlowRecordDao.delete_flow_info(db, flow_data['id'], query_model.action_id)
        # 新增审核记录
        record = OaFlowRecordBaseModel()
        record.action_id = query_model.action_id,
        record.check_table = flow_cate['check_table'],
        record.step_id = 0,
        record.check_uid = user_id,
        record.flow_id = flow_data['id'],
        record.check_time = datetime.now().timestamp(),
        record.check_status = 0,
        record.check_files = query_model.check_files if query_model.check_files else '',
        record.content = query_model.content
        await FlowRecordDao.add(db, record)

        # 修改各个表中的审核信息，添加审核步骤信息
        # 固定审批
        if query_model.check_uids is None:
            step = []
            sort = 0
            flow_name = ''
            check_position_id = 0
            check_uids = ''
            flow_steps = json.loads(flow_data['flow_list'])
            for flow_step in flow_steps:
                if flow_step['check_role'] == '1':
                    check_uids = await DeptDao.get_dept_manages(db, user_id,False)
                    if check_uids:
                        check_uids = ','.join(str(uid) for uid in check_uids)
                    flow_name = '当前部门负责人'
                    check_position_id = 0
                if flow_step['check_role'] == '2':
                    check_uids = await DeptDao.get_dept_manages(db, user_id, True)
                    if check_uids:
                        check_uids = ','.join(str(uid) for uid in check_uids)
                    flow_name = '上级部门负责人'
                    check_position_id = 0
                if flow_step['check_role'] == '3':
                    check_position = await PostDao.get_post_by_id(db, flow_step['check_position_id'])
                    check_uids = await UserDao.get_user_by_post_id(db, flow_step['check_position_id'])
                    if check_uids:
                        check_uids = ','.join(str(uid) for uid in check_uids)
                    else:
                        check_uids = ''
                    flow_name = check_position.post_name
                    check_position_id = check_position.post_id
                if flow_step['check_role'] == '4':
                    flow_name = '指定成员'
                    check_position_id = 0
                    check_uids = flow_step['check_uids']
                if flow_step['check_role'] == '5':
                    flow_name = '指定成员'
                    check_position_id = 0
                    check_uids = flow_step['check_uids']
                    check_type = 1
                st = OaFlowStepBaseModel()
                st.action_id = query_model.action_id
                st.flow_id = flow_data['id']
                st.flow_name = flow_name
                st.check_position_id = check_position_id
                st.check_role = int(flow_step['check_role'])
                st.check_uids = check_uids
                st.create_time = int(datetime.now().timestamp())
                st.sort = sort
                st.check_types = flow_step['check_types']
                step.append(st)
                sort += 1
            if step is None:
                return CrudResponseModel(is_success=False, message='审批流程设置有问题，无法提交审批申请，请联系HR或者管理员重新设置审批流程')
            result = await OaFlowStepDao.add_flow_step(db, step)
            # 添加审核记录信息，修改表审核状态
            if result:
                await FlowRecordDao.add(db, record)
                update_dict = {
                    'check_flow_id': query_model.flow_id,
                    "check_step_sort": 0,
                    "check_status": 1,
                    "check_uids": ','.join(str(uid) for uid in step[0].check_uids) if step[0].check_uids else '',
                    "check_copy_uids": query_model.check_copy_uids if query_model.check_copy_uids else '',
                    "action_id": query_model.action_id
                }
                sql = 'update %s set check_flow_id = :check_flow_id,check_step_sort=:check_step_sort,check_status=:check_status,check_uids=:check_uids, check_copy_uids=:check_copy_uids where id = :action_id' % ('oa_'+ flow_cate['check_table'])
                # 更新表审核信息
                await CheckDao.execute_update_sql(db, sql, update_dict)

                #发送消息通知
                # todo
                return CrudResponseModel(is_success=True, message='操作成功')
            else:
                return CrudResponseModel(is_success=False, message='操作失败')
        # 自由审批
        if query_model.check_uids is not None:
            step = {
                'action_id': query_model.action_id,
                'flow_id': flow_data['id'],
                'flow_name': '自由审批',
                'check_uids': query_model.check_uids,
                'create_time': datetime.now().timestamp()
            }
            result = await OaFlowStepDao.add(db, step)
            if result:
                # 添加审核申请记录
                await FlowRecordDao.add(db, record)
                # 修改审核信息
                update_dict = {
                    'check_flow_id': query_model.check_flow_id,
                    "check_step_sort": 0,
                    "check_status": 1,
                    "check_uids": ','.join(str(uid) for uid in step['check_uids']),
                    "check_copy_uids": query_model.check_copy_uids,
                    "action_id": query_model.action_id
                }
                sql = 'update %s set check_flow_id = :check_flow_id,check_step_sort=:check_step_sort,check_status=:check_status,check_uids=:check_uids, check_copy_uids=:check_copy_uids where id = :action_id' % ('oa_'+ flow_cate['check_table'])
                await CheckDao.execute_update_sql(db, sql, update_dict)
                # 发送消息通知
                # todo
            return CrudResponseModel(is_success=True, message='操作成功')
        else:
            return CrudResponseModel(is_success=False, message='操作失败')

    @classmethod
    async def get_flow_nodes(cls, db: AsyncSession, action_id : int, flow_id: int, dept_id : int, user_id: int) -> list[dict]:
        """
        获取审核节点
        :param db:
        :param check_table: 审核表名
        :param action_id: 审核表id
        :param flow_id: 流程id
        :param dept_id: 部门id
        :param user_id
        :return: 返回审核节点信息
        """
        flow = await OaFlowDao.get_flow_detail(db, flow_id)

        flow_cate = await FlowCateDao.get_flow_cate_info(db, flow.cate_id)
        if action_id == 0:
            flow_list = await OaFlowDao.get_flow_by_cate_id_dept_id(db, flow_cate.id, dept_id)
            flow_list = [dict(obj) for obj in flow_list]
            for flow in flow_list:
                flow['is_copy'] = flow_cate.is_copy
            return flow_list
        else:
            check_table = flow_cate.check_table
            detail = await cls.get_check_table_detail(db, check_table, action_id)
            detail = dict(detail)

            # 创建人
            is_creater = 0
            if detail['admin_id'] == user_id:
                is_creater = 1
            detail['is_creater'] = is_creater
            detail['admin_name'] = await UserDao.get_user_name_by_user_id(db, [detail['admin_id']])
            detail['nick_name'] = await UserDao.get_nick_name_by_user_id(db, [detail['admin_id']])


            # 当前审批人
            is_checker= 0
            if user_id in detail['check_uids'].split(','):
                is_checker = 1
            detail['is_checker'] = is_checker
            detail['is_copy'] = flow_cate.is_copy
            detail['is_file'] = flow_cate.is_file
            detail['is_export'] = flow_cate.is_export
            detail['is_back'] = flow_cate.is_back
            detail['is_reversed'] = flow_cate.is_reversed

            # 审批记录
            records = await FlowRecordDao.get_flow_record_by_action_table(db, action_id, check_table)
            records_dict = []
            for rec in records:
                rec = dict(rec)['OaFlowRecord'].to_dict()
                rec['check_time_str'] = format_timestamp(rec['check_time'])
                rec['check_status_str'] = '提交'
                if rec['check_status'] == 1:
                    rec['check_status_str'] = '通过'
                elif rec['check_status'] == 2:
                    rec['check_status_str'] = '驳回'
                elif rec['check_status'] == 3:
                    rec['check_status_str'] = '撤销'
                elif rec['check_status'] == 4:
                    rec['check_status_str'] = '反确认'
                if rec['check_files'] is not None:
                    rec['check_files_str'] = await FileDAO.get_file_by_ids(rec['check_files'], db)
                records_dict.append(rec)
            detail['records'] = records_dict
            if detail['check_status'] == 0 or detail['check_status'] == 4:
                # 如果审核状态为0或4，则需要获取审核步骤信息
                flow_list = await OaFlowDao.get_flow_by_cate_id_dept_id(db, flow_cate.id, dept_id)
                flows = []
                for flow in flow_list:
                    flow = flow.to_dict()
                    flows.append(flow)
                detail['flow'] = flows
            else:
                # 当前审核人
                detail['check_unames'] = await UserDao.get_user_name_by_user_id(db, detail['check_uids'].split(','))
                # 抄送人
                detail['copy_name'] = await UserDao.get_user_name_by_user_id(db, detail['check_copy_uids'].split(','))
                # 审核节点步骤
                nodes = await OaFlowStepDao.get_step_by_action_id_flow_id_list(db, action_id, flow_id)
                node_list = []
                for node in nodes:
                    node_dict = node.to_dict()
                    node_list.append(node_dict)
                for node in node_list:
                    if node['check_uids'] is None or node['check_uids'] == '':
                        check_ids = []
                    else:
                        check_ids = [int(id) for id in node['check_uids'].split(',')]

                    check_user_info = await UserDao.get_user_name_id_avatar_by_user_id(db, check_ids)
                    check_user_info = [dict(obj) for obj in check_user_info]
                    for user_info in check_user_info:
                        user_info['check_time'] = 0
                        user_info['content'] = ''
                        user_info['check_status'] = 0
                        steps = await FlowRecordDao.get_flow_record_by_check_uid_step_id(db, user_info['user_id'], flow_id)
                        if steps is not None and len(steps) > 0:
                            checked = steps[0]['OaFlowRecord'].to_dict()
                            user_info['check_time'] = format_timestamp(checked['check_time'])
                            user_info['content'] = checked['content']
                            user_info['check_status'] = checked['check_status']
                    node['check_user_info'] = check_user_info
                    if node['check_position_id'] is not None:
                        node['check_position_name'] = await UserDao.get_user_by_post_id(db, node['check_position_id'])
                    else:
                        node['check_position_name'] = ''
                    check_list = []
                    for check in records:
                        check = dict(check)
                        check.update(check['OaFlowRecord'].to_dict())
                        check.pop('OaFlowRecord')
                        if check['step_id'] ==node['id']:
                            check_list.append(check)
                    node['check_list'] = check_list
                detail['nodes'] = node_list
                # 当前审核节点
                step = await OaFlowStepDao.get_step_by_action_id_flow_id_sort(db,action_id, flow_id, detail['check_step_sort'])
                step = step.to_dict()
                detail['step'] = step
            return ModelConverter.convert_to_camel_case(detail)

    @classmethod
    async def skip_check(cls, db: AsyncSession, query_model: OaFlowCheckBaseModel, user_id: int):
        """
        跳过审核步骤
        :param db:
        :param query_model:
        :param user_id:
        :return:
        """
        if user_id != 1:
            return CrudResponseModel(is_success=False,message="您没有操作此功能权限，请使用管理员账号操作！")
        if query_model.check_status != 1:
            return CrudResponseModel(is_success=False,message="提交审核状态不支持此功能")
        flow = await OaFlowDao.get_flow_detail(db, query_model.flow_id)
        flow_cate = await FlowCateDao.get_flow_cate_info(db, flow.cate_id)
        subject = flow_cate.title
        action_id = query_model.action_id
        check_table = flow_cate.check_table
        check_step_sort = 0
        check_uids = None
        step = 0
        check_status = 0

        # 审核内容详情
        sql = 'select * from %s where id = :id' % ('oa_' + check_table)
        detail = await CheckDao.execute_row_sql(db, sql, {'id': action_id})
        if not detail:
            return CrudResponseModel(is_success=False, message='审核内容详情为空')

        # 当前节点审核详情
        step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id, detail['check_flow_id'],
                                                                 detail['check_step_sort'])
        step_id = step.id
        if not step:
            return CrudResponseModel(is_success=True, message='审核已结束')

        # 跳过审核步骤
        if step.check_role == 0:
            # 自由人审批
            if query_model.check_node == 2:
                next_step = detail['check_step'] + 1
                new_step = OaFlowStep(
                    action_id=action_id,
                    sort=next_step,
                    flow_id=detail['check_flow_id'],
                    check_uid=user_id,
                    create_time=datetime.now().timestamp()
                )
                # 更新当前节点审核人
                await OaFlowStepDao.add(db, new_step)
                # 下一步审核步骤
                step = new_step
                check_status = 1
            else:
                check_status = 2
                check_uids = ''
        else:
            # 查询当前步骤审批记录
            check_count = await FlowRecordDao.get_count_by_action_id_flow_id_step_id(db, action_id,
                                                                                     detail['check_flow_id'],
                                                                                     detail['check_step_sort'])
            flow_count = step.check_uids.split(',').__len__()
            check_status = 1
            check_uids = detail['check_uids'] + ',' + str(user_id)

            if ((check_count + 1) >= flow_count and step.check_types == 1) or step.check_types == 2:
                # 会签
                next_step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id,
                                                                              detail['check_flow_id'],
                                                                              detail['check_step_sort'] + 1)
                if next_step:
                    # 存在下一步审核
                    if next_step.check_role == 1:
                        check_uids = await DeptDao.get_dept_manages(detail['admin_id'], False)
                    elif next_step.check_role == 2:
                        check_uids = await DeptDao.get_dept_manages(detail['admin_id'], True)
                    elif next_step.check_role == 3:
                        uids = await UserDao.get_user_by_post_id(db, next_step.check_position_id)
                        check_uids = ','.join(str(uid) for uid in uids)
                    else:
                        check_uids = next_step.check_uids
                    check_step_sort = detail['check_step_sort'] + 1
                    check_status = 1
                else:
                    check_status = 2
                    check_uids = ''

        if check_status == 1 and check_uids is None:
            return CrudResponseModel(is_success=False,
                                     message="找不到下一步的审批人，该审批流程设置有问题，请联系HR或者管理员")
        # 添加历史审核人
        if detail['check_history_uids'] is None:
            check_history_uids = user_id
        else:
            check_history_uids = detail['check_history_uids'] + ',' + str(user_id)
        # 更新审核状态
        result = await cls.update_table_check(db, check_table, action_id, check_step_sort, check_uids, check_status,
                                              check_history_uids)
        if result:
            record = OaFlowRecordBaseModel()
            record.action_id = action_id,
            record.check_table = check_table,
            record.step_id = step_id,
            record.check_uid = user_id,
            record.flow_id = detail['check_flow_id'],
            record.check_time = datetime.now().timestamp(),
            record.check_files = query_model.check_files,
            record.check_status = check_status,
            record.content = query_model.content
            record.check_files = query_model.check_files if query_model.check_files is not None else ''
            # 添加审批记录
            await FlowRecordDao.add(db, record)

            # 添加审核日志
            # todo

            # 发送系统消息
            # todo
            return CrudResponseModel(is_success=True, data={'subject': subject, 'step': step}, message='审核成功')
        else:
            return CrudResponseModel(is_success=False, message='审核失败')




