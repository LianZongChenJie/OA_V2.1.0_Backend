from module_admin.dao.log_dao import OperationLogDao, OaAdminLogCountDao
from config.database import AsyncSessionLocal

async def job():
    """
    统计每天操作日志数量
    :return:
    """
    async with AsyncSessionLocal() as query_db:
        try:
            oper_count = await OperationLogDao.get_last_day_log_count(query_db)
            print(f'操作日志数量: {oper_count}')

            if oper_count:
                await OaAdminLogCountDao.add_last(query_db, oper_count)

            await query_db.commit()  # 提交事务
            print('日志统计任务执行成功')

        except Exception as e:
            await query_db.rollback()  # 出错回滚
            print(f'日志统计任务执行失败: {e}')
            raise
        finally:
            await query_db.close()  # 关闭会话


