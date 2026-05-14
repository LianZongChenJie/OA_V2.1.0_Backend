from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_contract.dao.contract_api_dao import ContractApiDao
from module_contract.entity.vo.contract_api_vo import SetStopModel, SetVoidModel
from utils.log_util import logger


class ContractApiService:
    """
    合同API服务层
    """

    @classmethod
    async def set_contract_stop_services(
            cls, request: Request, query_db: AsyncSession, set_stop: SetStopModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        设置合同中止状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param set_stop: 设置中止参数对象
        :param current_user_id: 当前用户 ID（操作人）
        :return: 操作结果
        """
        contract_type = set_stop.type.lower()

        # 校验合同类型
        if contract_type not in ['sale', 'purchase']:
            raise ServiceException(message=f'不支持的合同类型: {set_stop.type}，请使用 sale 或 purchase')

        try:
            # 检查合同是否存在
            existing_contract = await ContractApiDao.get_contract_by_id(query_db, contract_type, set_stop.id)
            if not existing_contract:
                contract_name = '销售合同' if contract_type == 'sale' else '采购合同'
                raise ServiceException(message=f'{contract_name}不存在')

            # 中止操作
            if set_stop.stop_status == 1:
                # 检查是否已归档（已归档合同不能中止）
                if existing_contract.get('archive_time') and existing_contract['archive_time'] > 0:
                    raise ServiceException(message='该合同已归档，无法中止')

                # 中止时备注必填
                if not set_stop.stop_remark or not set_stop.stop_remark.strip():
                    raise ServiceException(message='中止时必须填写中止备注')

                # 执行中止操作
                current_time = int(datetime.now().timestamp())
                result = await ContractApiDao.set_contract_stop(
                    query_db,
                    contract_type,
                    set_stop.id,
                    {
                        'stop_uid': current_user_id,
                        'stop_time': current_time,
                        'stop_remark': set_stop.stop_remark
                    }
                )

                if result > 0:
                    await query_db.commit()
                    logger.info(f'{contract_type}合同中止成功 - ID: {set_stop.id}, 操作人: {current_user_id}')
                    return CrudResponseModel(is_success=True, message='操作成功，合同已转入到中止合同列表')
                else:
                    raise ServiceException(message='中止失败')

            # 反中止操作
            elif set_stop.stop_status == 0:
                # 检查是否已中止
                if not existing_contract.get('stop_time') or existing_contract['stop_time'] == 0:
                    raise ServiceException(message='该合同未中止，无需反中止')

                # 执行反中止操作
                result = await ContractApiDao.set_contract_stop(
                    query_db,
                    contract_type,
                    set_stop.id,
                    {
                        'stop_uid': 0,
                        'stop_time': 0,
                        'stop_remark': ''
                    }
                )

                if result > 0:
                    await query_db.commit()
                    logger.info(f'{contract_type}合同反中止成功 - ID: {set_stop.id}, 操作人: {current_user_id}')
                    return CrudResponseModel(is_success=True, message='操作成功，合同已从中止合同列表转出')
                else:
                    raise ServiceException(message='反中止失败')

            else:
                raise ServiceException(message='无效的中止状态，请使用 1(中止) 或 0(反中止)')

        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'{contract_type}合同中止操作失败: {str(e)}', exc_info=True)
            raise e

    @classmethod
    async def set_contract_void_services(
            cls, request: Request, query_db: AsyncSession, set_void: SetVoidModel, current_user_id: int
    ) -> CrudResponseModel:
        """
        设置合同作废状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param set_void: 设置作废参数对象
        :param current_user_id: 当前用户 ID（操作人）
        :return: 操作结果
        """
        contract_type = set_void.type.lower()

        # 校验合同类型
        if contract_type not in ['sale', 'purchase']:
            raise ServiceException(message=f'不支持的合同类型: {set_void.type}，请使用 sale 或 purchase')

        try:
            # 检查合同是否存在
            existing_contract = await ContractApiDao.get_contract_by_id(query_db, contract_type, set_void.id)
            if not existing_contract:
                contract_name = '销售合同' if contract_type == 'sale' else '采购合同'
                raise ServiceException(message=f'{contract_name}不存在')

            # 作废操作
            if set_void.void_status == 1:
                # 检查是否已归档（已归档合同不能作废）
                if existing_contract.get('archive_time') and existing_contract['archive_time'] > 0:
                    raise ServiceException(message='该合同已归档，无法作废')

                # 作废时备注必填
                if not set_void.void_remark or not set_void.void_remark.strip():
                    raise ServiceException(message='作废时必须填写作废备注')

                # 执行作废操作
                current_time = int(datetime.now().timestamp())
                result = await ContractApiDao.set_contract_void(
                    query_db,
                    contract_type,
                    set_void.id,
                    {
                        'void_uid': current_user_id,
                        'void_time': current_time,
                        'void_remark': set_void.void_remark
                    }
                )

                if result > 0:
                    await query_db.commit()
                    logger.info(f'{contract_type}合同作废成功 - ID: {set_void.id}, 操作人: {current_user_id}')
                    return CrudResponseModel(is_success=True, message='操作成功，合同已转入到作废合同列表')
                else:
                    raise ServiceException(message='作废失败')

            # 反作废操作
            elif set_void.void_status == 0:
                # 检查是否已作废
                if not existing_contract.get('void_time') or existing_contract['void_time'] == 0:
                    raise ServiceException(message='该合同未作废，无需反作废')

                # 执行反作废操作
                result = await ContractApiDao.set_contract_void(
                    query_db,
                    contract_type,
                    set_void.id,
                    {
                        'void_uid': 0,
                        'void_time': 0,
                        'void_remark': ''
                    }
                )

                if result > 0:
                    await query_db.commit()
                    logger.info(f'{contract_type}合同反作废成功 - ID: {set_void.id}, 操作人: {current_user_id}')
                    return CrudResponseModel(is_success=True, message='操作成功，合同已从作废合同列表转出')
                else:
                    raise ServiceException(message='反作废失败')

            else:
                raise ServiceException(message='无效的作废状态，请使用 1(作废) 或 0(反作废)')

        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'{contract_type}合同作废操作失败: {str(e)}', exc_info=True)
            raise e
