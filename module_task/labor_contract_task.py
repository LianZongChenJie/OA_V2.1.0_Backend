from config.database import AsyncSessionLocal
from module_personnel.dao.labor_contract_dao import LaborContractDao
from utils.log_util import logger


async def job():
    """
    合同到期变更合同状态定时任务
    每天凌晨1点执行
    :return:
    """
    async with AsyncSessionLocal() as query_db:
        try:
            contract_ids = await LaborContractDao.get_expire_contract(query_db)
            change_count = 0
            if contract_ids:
                change_count = await LaborContractDao.change_expire_contract_status(query_db, contract_ids)
            logger.info(f'合同到期任务执行成功,共变更{change_count}本合同状态')
        except Exception as e:
            await query_db.rollback()  # 出错回滚
            logger.error(f'合同到期任务执行失败: {e}')
            raise
        finally:
            await query_db.close()  # 关闭会话