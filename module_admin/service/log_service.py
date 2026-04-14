import asyncio
import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import Request
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from config.database import AsyncSessionLocal
from config.env import LogConfig
from exceptions.exception import ServiceException
from middlewares.trace_middleware.ctx import TraceCtx
from module_admin.dao.log_dao import LoginLogDao, OperationLogDao
from module_admin.entity.do.log_do import SysOperLog
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.log_vo import (
    DeleteLoginLogModel,
    DeleteOperLogModel,
    LogininforModel,
    LoginLogPageQueryModel,
    OperLogModel,
    OperLogPageQueryModel,
    SimpleOperLogModel,
    UnlockUser,
)
from module_admin.service.dict_service import DictDataService
from utils.excel_util import ExcelUtil
from utils.log_util import logger


class OperationLogService:
    """
    操作日志管理模块服务层
    """

    @classmethod
    async def get_operation_log_list_services(
        cls, query_db: AsyncSession, query_object: OperLogPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取操作日志列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 操作日志列表信息对象
        """
        operation_log_list_result = await OperationLogDao.get_operation_log_list(query_db, query_object, is_page)

        return operation_log_list_result

    @classmethod
    async def get_simple_operation_log_list_services(
        cls, query_db: AsyncSession, page: int = 1, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        获取简化版操作日志列表（用于首页展示）

        :param query_db: orm对象
        :param page: 页码
        :param limit: 每页数量
        :return: 简化版操作日志列表
        """
        offset = (page - 1) * limit
        
        # 查询操作日志，关联用户表获取用户ID
        query = (
            select(SysOperLog.oper_id, SysOperLog.oper_name, SysOperLog.title, 
                   SysOperLog.business_type, SysOperLog.oper_time, SysUser.user_id)
            .join(SysUser, SysUser.user_name == SysOperLog.oper_name, isouter=True)
            .order_by(SysOperLog.oper_time.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await query_db.execute(query)
        rows = result.fetchall()
        
        log_list = []
        now = datetime.now()
        
        for row in rows:
            oper_id, oper_name, title, business_type, oper_time, user_id = row
            
            # 映射业务类型为操作类型
            type_map = {
                1: 'add',      # 新增
                2: 'edit',     # 修改
                3: 'delete',   # 删除
                4: 'grant',    # 授权
                5: 'export',   # 导出
                6: 'import',   # 导入
                7: 'force',    # 强退
                8: 'genCode',  # 生成代码
                9: 'clean',    # 清空数据
            }
            log_type = type_map.get(business_type, 'other') if business_type else 'other'
            
            # 映射业务类型为中文动作
            action_map = {
                1: '新增',
                2: '编辑',
                3: '删除',
                4: '授权',
                5: '导出',
                6: '导入',
                7: '强退',
                8: '生成代码',
                9: '清空数据',
            }
            action = action_map.get(business_type, '操作') if business_type else '操作'
            
            # 计算相对时间
            if oper_time:
                diff_seconds = (now - oper_time).total_seconds()
                if diff_seconds < 60:
                    times = f'{int(diff_seconds)}秒前'
                elif diff_seconds < 3600:
                    times = f'{int(diff_seconds / 60)}分钟前'
                elif diff_seconds < 86400:
                    times = f'{int(diff_seconds / 3600)}小时前'
                else:
                    times = f'{int(diff_seconds / 86400)}天前'
            else:
                times = ''
            
            # 生成内容描述
            content = f'{oper_name}{action}了{title}' if oper_name and title else ''
            
            log_item = {
                'id': oper_id,
                'uid': user_id or 0,
                'type': log_type,
                'subject': title or '',
                'action': action,
                'create_time': int(oper_time.timestamp()) if oper_time else 0,
                'name': oper_name or '',
                'content': content,
                'times': times,
            }
            log_list.append(log_item)
        
        return log_list

    @classmethod
    async def delete_operation_log_services(
        cls, query_db: AsyncSession, operation_log: DeleteOperLogModel
    ) -> CrudResponseModel:
        """
        删除操作日志信息 service

        :param query_db: orm对象
        :param operation_log: 删除操作日志对象
        :return: 删除操作日志校验结果
        """
        if operation_log.oper_ids:
            oper_ids = operation_log.oper_ids.split(',')
            try:
                for oper_id in oper_ids:
                    await OperationLogDao.delete_operation_log_dao(
                        query_db, OperLogModel(operId=int(oper_id))
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入日志id为空')

    @classmethod
    async def clear_operation_log_services(cls, query_db: AsyncSession) -> CrudResponseModel:
        """
        清空操作日志信息 service

        :param query_db: orm对象
        :return: 清空操作日志校验结果
        """
        try:
            await OperationLogDao.clear_operation_log_dao(query_db)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='清空成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def export_operation_log_list_services(
        cls, request: Request, operation_log_list: list[dict[str, Any]]
    ) -> bytes:
        """
        导出操作日志信息 service

        :param request: Request对象
        :param operation_log_list: 操作日志列表信息
        :return: 操作日志列表excel二进制数据
        """
        operation_type_list = await DictDataService.query_dict_data_list_from_cache_services(
            request.app.state.redis, dict_type='sys_oper_type'
        )
        operation_type_option = [
            {'label': item.get('dictLabel'), 'value': item.get('dictValue')} for item in operation_type_list
        ]
        operation_type_option_dict = {item.get('value'): item for item in operation_type_option}

        mapping_dict = {
            'operId': '日志编号',
            'title': '系统模块',
            'businessType': '操作类型',
            'method': '方法名称',
            'requestMethod': '请求方式',
            'operatorType': '操作类别',
            'operName': '操作人员',
            'deptName': '部门名称',
            'operUrl': '请求URL',
            'operIp': '操作地址',
            'operLocation': '操作地点',
            'operParam': '请求参数',
            'jsonResult': '返回参数',
            'status': '操作状态',
            'errorMsg': '错误消息',
            'operTime': '操作日期',
            'costTime': '消耗时间（毫秒）',
        }

        for item in operation_log_list:
            if item.get('status') == 0:
                item['status'] = '成功'
            else:
                item['status'] = '失败'
            if str(item.get('businessType')) in operation_type_option_dict:
                item['businessType'] = operation_type_option_dict.get(str(item.get('businessType'))).get('label')
        binary_data = ExcelUtil.export_list2excel(operation_log_list, mapping_dict)

        return binary_data


class LoginLogService:
    """
    登录日志管理模块服务层
    """

    @classmethod
    async def get_login_log_list_services(
        cls, query_db: AsyncSession, query_object: LoginLogPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取登录日志列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 登录日志列表信息对象
        """
        operation_log_list_result = await LoginLogDao.get_login_log_list(query_db, query_object, is_page)

        return operation_log_list_result

    @classmethod
    async def delete_login_log_services(
        cls, query_db: AsyncSession, login_log: DeleteLoginLogModel
    ) -> CrudResponseModel:
        """
        删除登录日志信息 service

        :param query_db: orm对象
        :param login_log: 删除登录日志对象
        :return: 删除登录日志校验结果
        """
        if login_log.info_ids:
            info_ids = login_log.info_ids.split(',')
            try:
                for info_id in info_ids:
                    await LoginLogDao.delete_login_log_dao(
                        query_db, LogininforModel(infoId=int(info_id))
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入访问id为空')

    @classmethod
    async def clear_login_log_services(cls, query_db: AsyncSession) -> CrudResponseModel:
        """
        清空登录日志信息 service

        :param query_db: orm对象
        :return: 清空登录日志校验结果
        """
        try:
            await LoginLogDao.clear_login_log_dao(query_db)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='清空成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def unlock_user_services(cls, request: Request, unlock_user: UnlockUser) -> CrudResponseModel:
        """
        解锁用户服务

        :param request: Request对象
        :param unlock_user: 解锁用户对象
        :return: 解锁结果
        """
        redis_client = request.app.state.redis
        if not redis_client:
            raise ServiceException(message='Redis未连接')

        lock_key = f'account_lock:{unlock_user.user_name}'
        fail_count_key = f'pwd_err_cnt:{unlock_user.user_name}'

        await redis_client.delete(lock_key, fail_count_key)

        return CrudResponseModel(is_success=True, message=f'用户 {unlock_user.user_name} 解锁成功')

    @classmethod
    async def export_login_log_list_services(cls, login_log_list: list[dict[str, Any]]) -> bytes:
        """
        导出登录日志信息 service

        :param login_log_list: 登录日志列表信息
        :return: 登录日志列表excel二进制数据
        """
        mapping_dict = {
            'infoId': '访问编号',
            'userName': '用户名称',
            'ipaddr': '登录地址',
            'loginLocation': '登录地点',
            'browser': '浏览器',
            'os': '操作系统',
            'status': '登录状态',
            'msg': '操作信息',
            'loginTime': '登录时间',
        }

        for item in login_log_list:
            if item.get('status') == '0':
                item['status'] = '成功'
            else:
                item['status'] = '失败'

        binary_data = ExcelUtil.export_list2excel(login_log_list, mapping_dict)

        return binary_data


class LogQueueService:
    """
    日志队列服务
    """

    @classmethod
    async def _xadd_event(cls, redis_client: aioredis.Redis, stream: str, payload: dict, source: str) -> None:
        """
        向 Redis Stream 添加事件

        :param redis_client: Redis客户端
        :param stream: Stream名称
        :param payload: 事件负载
        :param source: 日志来源
        :return: None
        """
        if not redis_client:
            return

        request_id = payload.pop('requestId', '')
        trace_id = payload.pop('traceId', '')
        span_id = payload.pop('spanId', '')

        await redis_client.xadd(
            name=f'log_stream:{stream}',
            fields={
                'source': source,
                'request_id': request_id,
                'trace_id': trace_id,
                'span_id': span_id,
                'payload': json.dumps(payload, ensure_ascii=False, default=str),
            },
            maxlen=LogConfig.log_stream_maxlen,
            approximate=True,
        )

    @classmethod
    async def enqueue_login_log(cls, request: Request, login_log: LogininforModel, source: str) -> None:
        """
        登录日志入队

        :param request: Request对象
        :param login_log: 登录日志模型
        :param source: 日志来源
        :return: None
        """
        payload = login_log.model_dump(by_alias=True, exclude_none=True)
        await cls._xadd_event(request.app.state.redis, 'login', payload, source)

    @classmethod
    async def enqueue_operation_log(cls, request: Request, operation_log: OperLogModel, source: str) -> None:
        """
        操作日志入队

        :param request: Request对象
        :param operation_log: 操作日志模型
        :param source: 日志来源
        :return: None
        """
        payload = operation_log.model_dump(by_alias=True, exclude_none=True)
        await cls._xadd_event(request.app.state.redis, 'operation', payload, source)


class LogAggregatorService:
    """
    日志聚合消费服务
    """

    @classmethod
    async def consume_stream(cls, redis_client: aioredis.Redis) -> None:
        """
        消费日志流（统一入口）

        :param redis_client: Redis客户端
        :return: None
        """
        if not redis_client:
            logger.warning('Redis客户端未初始化，日志聚合服务停止')
            return

        logger.info('日志聚合服务启动')
        
        try:
            while True:
                try:
                    # 同时消费操作日志和登录日志
                    result = await redis_client.xread(
                        streams={'log_stream:operation': '0', 'log_stream:login': '0'},
                        count=10,
                        block=5000
                    )
                    
                    if not result:
                        continue
                    
                    for stream_name, messages in result:
                        for message_id, fields in messages:
                            try:
                                payload = json.loads(fields.get('payload', '{}'))
                                source = fields.get('source', '')
                                
                                if 'operation' in stream_name:
                                    await cls._process_operation_log(payload)
                                elif 'login' in stream_name:
                                    await cls._process_login_log(payload)
                                
                                # 删除已处理的消息
                                await redis_client.xdel(stream_name, message_id)
                                
                            except Exception as e:
                                logger.error(f'处理日志消息失败: {e}')
                                continue
                                
                except asyncio.CancelledError:
                    logger.info('日志聚合服务被取消')
                    break
                except Exception as e:
                    logger.error(f'消费日志流异常: {e}')
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            logger.info('日志聚合服务已停止')
        except Exception as e:
            logger.error(f'日志聚合服务异常退出: {e}')

    @classmethod
    async def _process_operation_log(cls, payload: dict) -> None:
        """
        处理操作日志

        :param payload: 日志数据
        :return: None
        """
        async with AsyncSessionLocal() as session:
            try:
                operation_log = OperLogModel(**payload)
                await OperationLogDao.add_operation_log_dao(session, operation_log)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f'保存操作日志失败: {e}')

    @classmethod
    async def _process_login_log(cls, payload: dict) -> None:
        """
        处理登录日志

        :param payload: 日志数据
        :return: None
        """
        async with AsyncSessionLocal() as session:
            try:
                login_log = LogininforModel(**payload)
                await LoginLogDao.add_login_log_dao(session, login_log)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f'保存登录日志失败: {e}')
