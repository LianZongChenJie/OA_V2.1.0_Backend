from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.do.dept_do import SysDept
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_administrative.dao.overtimes_dao import OvertimesDao
from module_administrative.entity.vo.overtimes_vo import (
    AddOvertimesModel,
    DeleteOvertimesModel,
    EditOvertimesModel,
    OvertimesModel,
    OvertimesPageQueryModel,
)
from module_personnel.dao.flow_record_dao import FlowRecordDao
from utils.camel_converter import ModelConverter
from utils.common_util import CamelCaseUtil


class OvertimesService:
    """
    加班记录管理服务层
    """

    @classmethod
    async def get_overtimes_list_services(
            cls, query_db: AsyncSession, query_object: OvertimesPageQueryModel, user_id: int, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取加班记录列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户 ID
        :param is_page: 是否开启分页
        :return: 加班记录列表信息对象
        """
        overtimes_list_result = await OvertimesDao.get_overtimes_list(query_db, query_object, user_id, is_page)

        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(overtimes_list_result, 'rows'):
            transformed_rows = []
            for row in overtimes_list_result.rows:
                transformed_dict = CamelCaseUtil.transform_result(row)
                
                # 格式化时间
                create_time = transformed_dict.get('createTime')
                if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                    if create_time > 1e12:
                        create_time_seconds = create_time / 1000
                    else:
                        create_time_seconds = create_time
                    transformed_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    transformed_dict['createTime'] = ''
                
                start_date = transformed_dict.get('startDate')
                if start_date and isinstance(start_date, (int, float)) and start_date > 0:
                    if start_date > 1e12:
                        start_date_seconds = start_date / 1000
                    else:
                        start_date_seconds = start_date
                    transformed_dict['startDate'] = datetime.fromtimestamp(start_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    transformed_dict['startDate'] = ''
                
                end_date = transformed_dict.get('endDate')
                if end_date and isinstance(end_date, (int, float)) and end_date > 0:
                    if end_date > 1e12:
                        end_date_seconds = end_date / 1000
                    else:
                        end_date_seconds = end_date
                    transformed_dict['endDate'] = datetime.fromtimestamp(end_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    transformed_dict['endDate'] = ''
                
                # 获取创建人姓名
                admin_id = transformed_dict.get('adminId')
                if admin_id and isinstance(admin_id, int) and admin_id > 0:
                    admin_user = await query_db.execute(
                        select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == admin_id)
                    )
                    user_info = admin_user.first()
                    if user_info:
                        transformed_dict['adminName'] = user_info.nick_name or user_info.user_name
                    else:
                        transformed_dict['adminName'] = ''
                else:
                    transformed_dict['adminName'] = ''
                
                # 获取部门名称
                did = transformed_dict.get('did')
                if did and isinstance(did, int) and did > 0:
                    dept = await query_db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id == did)
                    )
                    dept_info = dept.scalar_one_or_none()
                    transformed_dict['deptName'] = dept_info if dept_info else ''
                else:
                    transformed_dict['deptName'] = ''
                
                # 获取当前审批人姓名
                check_uids = transformed_dict.get('checkUids')
                if check_uids and isinstance(check_uids, str) and check_uids.strip():
                    uid_list = [int(uid.strip()) for uid in check_uids.split(',') if uid.strip().isdigit()]
                    if uid_list:
                        users_result = await query_db.execute(
                            select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(uid_list))
                        )
                        users = users_result.all()
                        transformed_dict['checkName'] = ','.join([u.nick_name or u.user_name for u in users])
                    else:
                        transformed_dict['checkName'] = ''
                else:
                    transformed_dict['checkName'] = ''
                
                transformed_rows.append(transformed_dict)

            overtimes_list_result.rows = transformed_rows

        return overtimes_list_result

    @classmethod
    async def add_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddOvertimesModel, user_id: int, dept_id: int
    ) -> CrudResponseModel:
        """
        新增加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增加班记录对象
        :param user_id: 用户ID
        :param dept_id: 部门ID
        :return: 新增加班记录校验结果
        """
        try:
            current_time = int(datetime.now().timestamp())
            overtimes_data = page_object.model_dump(
                exclude_unset=True,
                exclude={'admin_name', 'dept_name', 'check_name', 'records'}
            )

            # 处理 start_date
            if 'start_date' in overtimes_data:
                start_date_value = overtimes_data['start_date']
                if isinstance(start_date_value, str) and ('-' in start_date_value or ':' in start_date_value):
                    try:
                        dt = datetime.fromisoformat(start_date_value)
                        overtimes_data['start_date'] = int(dt.timestamp())
                    except ValueError:
                        overtimes_data['start_date'] = 0
                elif not start_date_value:
                    overtimes_data['start_date'] = 0
            
            # 处理 end_date
            if 'end_date' in overtimes_data:
                end_date_value = overtimes_data['end_date']
                if isinstance(end_date_value, str) and ('-' in end_date_value or ':' in end_date_value):
                    try:
                        dt = datetime.fromisoformat(end_date_value)
                        overtimes_data['end_date'] = int(dt.timestamp())
                    except ValueError:
                        overtimes_data['end_date'] = 0
                elif not end_date_value:
                    overtimes_data['end_date'] = 0

            # 验证结束时间不能小于开始时间
            if 'start_date' in overtimes_data and 'end_date' in overtimes_data:
                if overtimes_data['end_date'] < overtimes_data['start_date']:
                    raise ServiceException(message='结束时间不能小于开始时间')

            overtimes_data['create_time'] = current_time
            overtimes_data['update_time'] = current_time
            overtimes_data['delete_time'] = 0
            overtimes_data['admin_id'] = user_id
            overtimes_data['did'] = dept_id

            await OvertimesDao.add_overtimes_dao(query_db, overtimes_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditOvertimesModel
    ) -> CrudResponseModel:
        """
        编辑加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑加班记录对象
        :return: 编辑加班记录校验结果
        """
        if page_object.id:
            try:
                overtimes_data = page_object.model_dump(
                    exclude_unset=True,
                    exclude={'id', 'admin_name', 'dept_name', 'check_name', 'records', 'create_time', 'delete_time'}
                )
                
                # 处理 start_date
                if 'start_date' in overtimes_data:
                    start_date_value = overtimes_data['start_date']
                    if isinstance(start_date_value, str) and ('-' in start_date_value or ':' in start_date_value):
                        try:
                            dt = datetime.fromisoformat(start_date_value)
                            overtimes_data['start_date'] = int(dt.timestamp())
                        except ValueError:
                            overtimes_data['start_date'] = 0
                    elif not start_date_value:
                        overtimes_data['start_date'] = 0
                
                # 处理 end_date
                if 'end_date' in overtimes_data:
                    end_date_value = overtimes_data['end_date']
                    if isinstance(end_date_value, str) and ('-' in end_date_value or ':' in end_date_value):
                        try:
                            dt = datetime.fromisoformat(end_date_value)
                            overtimes_data['end_date'] = int(dt.timestamp())
                        except ValueError:
                            overtimes_data['end_date'] = 0
                    elif not end_date_value:
                        overtimes_data['end_date'] = 0

                # 验证结束时间不能小于开始时间
                if 'start_date' in overtimes_data and 'end_date' in overtimes_data:
                    if overtimes_data['end_date'] < overtimes_data['start_date']:
                        raise ServiceException(message='结束时间不能小于开始时间')

                overtimes_data['update_time'] = int(datetime.now().timestamp())

                await OvertimesDao.edit_overtimes_dao(query_db, page_object.id, overtimes_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='加班记录不存在')

    @classmethod
    async def delete_overtimes_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteOvertimesModel
    ) -> CrudResponseModel:
        """
        删除加班记录信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除加班记录对象
        :return: 删除加班记录校验结果
        """
        if page_object.id:
            try:
                overtimes = await cls.overtimes_detail_services(query_db, page_object.id)
                if not overtimes.id:
                    raise ServiceException(message='加班记录不存在')

                await OvertimesDao.delete_overtimes_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入加班记录 id 为空')

    @classmethod
    async def overtimes_detail_services(cls, query_db: AsyncSession, overtimes_id: int) -> OvertimesModel:
        """
        获取加班记录详细信息 service

        :param query_db: orm 对象
        :param overtimes_id: 加班记录 ID
        :return: 加班记录 ID 对应的信息
        """
        result = await OvertimesDao.get_overtimes_detail_by_id(query_db, overtimes_id)

        if result:
            overtimes_dict = CamelCaseUtil.transform_result(result)
            
            # 格式化开始日期
            start_date = overtimes_dict.get('startDate')
            if start_date and isinstance(start_date, (int, float)) and start_date > 0:
                if start_date > 1e12:
                    start_date_seconds = start_date / 1000
                else:
                    start_date_seconds = start_date
                overtimes_dict['startDate'] = datetime.fromtimestamp(start_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
            else:
                overtimes_dict['startDate'] = ''
            
            # 格式化结束日期
            end_date = overtimes_dict.get('endDate')
            if end_date and isinstance(end_date, (int, float)) and end_date > 0:
                if end_date > 1e12:
                    end_date_seconds = end_date / 1000
                else:
                    end_date_seconds = end_date
                overtimes_dict['endDate'] = datetime.fromtimestamp(end_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
            else:
                overtimes_dict['endDate'] = ''
            
            # 格式化创建时间
            create_time = overtimes_dict.get('createTime')
            if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                if create_time > 1e12:
                    create_time_seconds = create_time / 1000
                else:
                    create_time_seconds = create_time
                overtimes_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            else:
                overtimes_dict['createTime'] = ''
            
            # 格式化更新时间
            update_time = overtimes_dict.get('updateTime')
            if update_time and isinstance(update_time, (int, float)) and update_time > 0:
                if update_time > 1e12:
                    update_time_seconds = update_time / 1000
                else:
                    update_time_seconds = update_time
                overtimes_dict['updateTime'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            else:
                overtimes_dict['updateTime'] = ''
            
            # 格式化删除时间
            delete_time = overtimes_dict.get('deleteTime')
            if delete_time and isinstance(delete_time, (int, float)) and delete_time > 0:
                if delete_time > 1e12:
                    delete_time_seconds = delete_time / 1000
                else:
                    delete_time_seconds = delete_time
                overtimes_dict['deleteTime'] = datetime.fromtimestamp(delete_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            else:
                overtimes_dict['deleteTime'] = ''
            
            # 获取创建人姓名
            admin_id = overtimes_dict.get('adminId')
            if admin_id and isinstance(admin_id, int) and admin_id > 0:
                try:
                    admin_user = await query_db.execute(
                        select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id == admin_id)
                    )
                    user_info = admin_user.first()
                    if user_info:
                        overtimes_dict['adminName'] = user_info.nick_name or user_info.user_name
                    else:
                        overtimes_dict['adminName'] = ''
                except Exception as e:
                    logger.error(f"查询创建人失败: {e}")
                    overtimes_dict['adminName'] = ''
            else:
                overtimes_dict['adminName'] = ''
            
            # 获取部门名称
            did = overtimes_dict.get('did')
            if did and isinstance(did, int) and did > 0:
                try:
                    dept = await query_db.execute(
                        select(SysDept.dept_name).where(SysDept.dept_id == did)
                    )
                    dept_info = dept.scalar_one_or_none()
                    overtimes_dict['deptName'] = dept_info if dept_info else ''
                except Exception as e:
                    logger.error(f"查询部门失败: {e}")
                    overtimes_dict['deptName'] = ''
            else:
                overtimes_dict['deptName'] = ''
            
            # 获取当前审批人姓名
            check_uids = overtimes_dict.get('checkUids')
            if check_uids and isinstance(check_uids, str) and check_uids.strip():
                try:
                    uid_list = [int(uid.strip()) for uid in check_uids.split(',') if uid.strip().isdigit()]
                    if uid_list:
                        users_result = await query_db.execute(
                            select(SysUser.nick_name, SysUser.user_name).where(SysUser.user_id.in_(uid_list))
                        )
                        users = users_result.all()
                        overtimes_dict['checkName'] = ','.join([u.nick_name or u.user_name for u in users])
                    else:
                        overtimes_dict['checkName'] = ''
                except Exception as e:
                    logger.error(f"查询审批人失败: {e}")
                    overtimes_dict['checkName'] = ''
            else:
                overtimes_dict['checkName'] = ''
            
            # 获取审批记录
            flow_id = overtimes_dict.get('checkFlowId')
            if flow_id and isinstance(flow_id, int) and flow_id > 0:
                try:
                    records = await FlowRecordDao.get_records_dict(db=query_db, action_id=overtimes_id, flow_id=flow_id)
                    # 将字段名转换为驼峰格式
                    if records:
                        records = CamelCaseUtil.transform_result(records)
                    overtimes_dict['records'] = records if records else []
                except Exception as e:
                    overtimes_dict['records'] = []
            else:
                overtimes_dict['records'] = []
            
            return OvertimesModel(**overtimes_dict)
        else:
            raise ServiceException(message=f'加班记录 ID {overtimes_id} 不存在')