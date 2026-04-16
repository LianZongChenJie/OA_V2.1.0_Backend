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
from module_basicdata.entity.vo.public.flow_vo import OaFlowCheckBaseModel
from common.vo import CrudResponseModel
from datetime import datetime

from module_personnel.dao.flow_record_dao import FlowRecordDao
from module_personnel.entity.do.flow_record_do import OaFlowRecord


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
        sql = 'update %s set(check_step_sort = :check_step_sort,check_status=:check_status,check_history_uids=:check_history_uids,check_uids=:check_uids) where id = :action_id' % check_table
        # 更新表审核信息
        result = await CheckDao.execute_update_sql(db, sql, update_dict)
        return result

    @classmethod
    async def flow_check(cls, db: AsyncSession, query_model: OaFlowCheckBaseModel, user_id: int):
        check_files = query_model.check_files
        flow_cate = await FlowCateDao.get_flow_cate_info_by_name(db, query_model.check_name)
        subject = flow_cate.title
        action_id = query_model.action_id
        check_table = flow_cate.check_table
        check_step_sort = 0
        check_uids = None
        step = 0
        check_status = 0

        # 审核内容详情
        sql = 'select * from %s where id = :id' % check_table
        detail = await CheckDao.execute_row_sql(db, sql, {'id':action_id})
        if not detail:
            return CrudResponseModel(is_success=False, message='审核内容详情为空')

        # 当前节点审核详情
        step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'])
        if not step:
            if query_model.check == 1:
                if user_id not in detail['check_uids'].keys():
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

                else:
                    # 查询当前步骤审批记录
                    check_count = FlowRecordDao.get_count_by_action_id_flow_id_step_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'])
                    flow_count = step.check_uids.split(',').__len__()
                    check_status = 1
                    uids_array = detail['check_uids'].split(',')
                    new_uids = uids_array + (user_id,)
                    check_uids = ','.join(new_uids)
                    if ((check_count + 1) >= flow_count and step.check_step ==1) or step.check_step == 2:
                        # 会签
                        next_step = await OaFlowStepDao.get_step_by_action_id_flow_id(db, action_id, detail['check_flow_id'], detail['check_step_sort'])
                        if next_step:
                            # 存在下一步审核
                            if next_step.check_role == 1:
                                check_uids = await DeptDao.get_dept_manages(detail['admin_id'])
                            elif next_step.check_role == 2:
                                check_uids = await DeptDao.get_dept_manages(detail['admin_id'], True)
                            elif next_step.check_role == 3:
                                uids = await UserDao.get_user_by_post_id(db,next_step.check_position_id)
                                check_uids = ','.join(uids)
                            else:
                                check_uids = next_step.check_uids
                            check_step_sort = detail['check_step_sort'] + 1
                            check_status = 1
                        else:
                            check_status = 2
                            check_uids = ''

                if check_status == 1 and query_model.check_uids is None:
                    return CrudResponseModel(is_success = False, message="找不到下一步的审批人，该审批流程设置有问题，请联系HR或者管理员")
                # 添加历史审核人
                if detail['check_history_uids'] is None:
                    check_history_uids = user_id
                else:
                    check_history_uids = detail['check_history_uids'] + ',' + user_id

                # 更新审核状态
                result = await cls.update_table_check(db, check_table, action_id, check_step_sort,check_uids, check_status, check_history_uids)
                if result:
                    record= OaFlowRecord(
                        action_id = action_id,
                        check_table = check_table,
                        step_id = step.id,
                        check_uid = user_id,
                        flow_id = detail['check_flow_id'],
                        check_time = datetime.now().timestamp(),
                        check_files = query_model.check_files,
                        check_status = check_status,
                        content = query_model.content
                    )
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
            elif query_model.check==2:
                check_uids = detail['check_uids'].split(',')
                if user_id not in check_uids:
                    return CrudResponseModel(is_success=False, message="您没有权限审核此审批")
                # 审核拒绝数据库操作
                check_status = 3

                # 添加历史审核人
                if not detail['check_history_uids']:
                    check_history_uids = user_id
                else:
                    check_history_uids = detail['check_history_uids']+ ','+ user_id
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
                    record = OaFlowRecord(
                        action_id=action_id,
                        check_table=check_table,
                        step_id=step.id,
                        check_uid=user_id,
                        flow_id=detail['check_flow_id'],
                        check_time=datetime.now().timestamp(),
                        check_files=query_model.check_files,
                        check_status=check_status,
                        content=query_model.content
                    )
                    # 添加审批记录
                    await FlowRecordDao.add(db, record)
                    if flow_cate.template_id > 0:
                        # 发送消息
                        # todo
                        # 记录操作日志
                        # todo
                        pass
                    return CrudResponseModel(is_success=True, message='操作成功！')
                else:
                    return CrudResponseModel(is_success=False, message='操作失败！')

            # 撤回审核
            elif query_model.check==3:
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
                    record = OaFlowRecord(
                        action_id=action_id,
                        check_table=check_table,
                        step_id=step.id,
                        check_uid=user_id,
                        flow_id=detail['check_flow_id'],
                        check_time=datetime.now().timestamp(),
                        check_files=query_model.check_files,
                        check_status=check_status,
                        content=query_model.content
                    )
                    await FlowRecordDao.add(db, record)
                    # 添加日志记录
                    # todo
                    return CrudResponseModel(is_success=True, message='操作成功！')
                else:
                    return CrudResponseModel(is_success=False, message='操作时哦白！')
            # 审核反确认，数据会带待提交状态
            elif query_model.check==4:
                check_status = 0
                check_uids = ''
                check_step_sort = 0
                check_history_uids = ''
                result = await cls.update_table_check(db, check_table, action_id, check_step_sort, check_uids,
                                                      check_status, check_history_uids)
                if result:
                    record = OaFlowRecord(
                        action_id=action_id,
                        check_table=check_table,
                        step_id=step.id,
                        check_uid=user_id,
                        flow_id=detail['check_flow_id'],
                        check_time=datetime.now().timestamp(),
                        check_files=query_model.check_files,
                        check_status=check_status,
                        content=query_model.content
                    )
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
        flow = await OaFlowDao.get_flow_detail(db, flow_id,user_id)
        if flow:
            if flow.flow_list:
                flow_list = json.loads(flow.flow_list)
                for flow_step in flow_list:
                    flow_step['check_position']= ''
                    if flow_step['check_role'] == 1:
                        check_uids = await DeptDao.get_dept_manages(db, user_id)
                    if flow_step['check_role'] == 2:
                        check_uids = await DeptDao.get_dept_manages(db, user_id, True)
                    if flow_step['check_role'] == 3:
                        check_position = PostDao.get_post_by_id(db, flow_step['check_position_id'])
                        check_user_ids = await UserDao.get_user_by_post_id(db, flow_step['check_position_id'])
                        check_uids = ''
                        for uid in check_user_ids:
                            if check_uids != '':
                                check_uids = check_uids + ',' + uid
                            else:
                                check_uids = uid
                    check_user_names = UserDao.get_user_name_by_user_id(db, check_uids.split(','))

                else:
                    return []
            # 抄送人信息
            data['copy_uids'] = flow.copy_uids
            data['copy_user_names'] = UserDao.get_user_name_by_user_id(db, flow.copy_uids.split(','))
        data['flow_list'] = flow.flow_list
        return data


