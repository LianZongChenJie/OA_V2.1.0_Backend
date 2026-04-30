from config.database import AsyncSessionLocal
from module_administrative.dao.msg_dao import MsgDao
from module_administrative.entity.do.msg_do import OaMsg
from module_dashboard.dao.plan_dao import PlanDao
from utils.log_util import logger
from utils.timeformat import int_time
from datetime import datetime


async def job():
    """
    日程提醒自动任务，轮询任务，每次轮询间隔30秒，将轮询前后15秒内需要提醒的任务查询出来，然后发送消息
    :return:
    """
    async with AsyncSessionLocal() as query_db:
        try:
            msg_list = []
            wait_send = await PlanDao.get_well_remind_plan(query_db)
            if wait_send:
                for plan in wait_send:
                    plan = dict(plan)
                    msg = OaMsg()
                    msg.title = f'工作计划提醒'
                    msg.template = 0
                    msg.content = f'你的工作计划：{plan["title"]},于{int_time(plan["start_time"])}开始'
                    msg.file_ids = plan["file_ids"]
                    msg.from_uid = 0
                    msg.to_uid = plan['admin_id']
                    msg.message_id = 0
                    msg.msg_id = 0
                    msg.is_star = 0
                    msg.read_time = 0
                    msg.create_time = int(datetime.now().timestamp())
                    msg.action_id = plan['id']
                    msg_list.append(msg)
                if msg_list:
                    await MsgDao.add_list(query_db, msg_list)
            logger.info(f'日程提醒任务执行成功,共发送{len(msg_list)}条消息')
        except Exception as e:
            await query_db.rollback()  # 出错回滚
            logger.error(f'日程提醒任务执行失败: {e}')
            raise
        finally:
            await query_db.close()  # 关闭会话