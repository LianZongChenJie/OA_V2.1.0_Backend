from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.meeting_dao import (
    MeetingOrderDao,
    MeetingRecordsDao,
    MeetingRoomDao,
)
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.meeting_do import OaMeetingRecords, OaMeetingRoom
from module_admin.entity.do.user_do import SysUser
from module_admin.entity.vo.meeting_vo import (
    AddMeetingOrderModel,
    AddMeetingRecordsModel,
    AddMeetingRoomModel,
    DeleteMeetingOrderModel,
    DeleteMeetingRecordsModel,
    DeleteMeetingRoomModel,
    EditMeetingOrderModel,
    EditMeetingRecordsModel,
    EditMeetingRoomModel,
    MeetingOrderPageQueryModel,
    MeetingRecordsPageQueryModel,
    MeetingRoomModel,
    MeetingRoomPageQueryModel,
    MeetingRoomStatusModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger

class MeetingRoomService:
    """
    会议室管理服务层
    """

    @classmethod
    async def check_meeting_room_title_unique_services(
            cls, query_db: AsyncSession, page_object: MeetingRoomModel
    ) -> bool:
        """
        校验会议室名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 会议室对象
        :return: 校验结果
        """
        room_id = -1 if page_object.id is None else page_object.id
        room = await MeetingRoomDao.get_meeting_room_detail_by_info(query_db, page_object.title)
        if room and room.id != room_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def get_meeting_room_list_services(
            cls, query_db: AsyncSession, query_object: MeetingRoomPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取会议室列表信息 service
        """
        room_list_result = await MeetingRoomDao.get_meeting_room_list(query_db, query_object, is_page)
        return CamelCaseUtil.transform_result(room_list_result)

    @classmethod
    async def add_meeting_room_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddMeetingRoomModel
    ) -> CrudResponseModel:
        """
        新增会议室信息 service
        """
        # 检查会议室名称是否已存在
        is_unique = await cls.check_meeting_room_title_unique_services(query_db, page_object)
        if not is_unique:
            raise ServiceException(message=f'新增会议室失败，会议室名称【{page_object.title}】已存在')
        
        try:
            current_time = int(datetime.now().timestamp())
            room_data = page_object.model_dump(exclude_unset=True)
            room_data['create_time'] = current_time
            room_data['update_time'] = current_time
            room_data['status'] = 1

            await MeetingRoomDao.add_meeting_room_dao(query_db, room_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_meeting_room_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditMeetingRoomModel
    ) -> CrudResponseModel:
        """
        编辑会议室信息 service
        """
        # 检查会议室名称是否已存在（排除当前会议室）
        is_unique = await cls.check_meeting_room_title_unique_services(query_db, page_object)
        if not is_unique:
            raise ServiceException(message=f'修改会议室失败，会议室名称【{page_object.title}】已存在')
        
        room_data = page_object.model_dump(exclude_unset=True)
        room_info = await cls.meeting_room_detail_services(query_db, page_object.id)

        if room_info.id:
            try:
                room_data['update_time'] = int(datetime.now().timestamp())
                await MeetingRoomDao.edit_meeting_room_dao(query_db, room_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='会议室不存在')

    @classmethod
    async def delete_meeting_room_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteMeetingRoomModel
    ) -> CrudResponseModel:
        """
        删除会议室信息 service
        """
        if page_object.id:
            try:
                room = await cls.meeting_room_detail_services(query_db, page_object.id)
                if not room.id:
                    raise ServiceException(message='会议室不存在')

                await MeetingRoomDao.delete_meeting_room_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入会议室 id 为空')

    @classmethod
    async def update_meeting_room_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: MeetingRoomStatusModel
    ) -> CrudResponseModel:
        """
        更新会议室状态 service
        """
        if page_object.id:
            try:
                room = await cls.meeting_room_detail_services(query_db, page_object.id)
                if not room.id:
                    raise ServiceException(message='会议室不存在')

                await MeetingRoomDao.update_meeting_room_status_dao(query_db, page_object.id, page_object.status)
                await query_db.commit()

                action_map = {0: '禁用', 1: '启用'}
                action = action_map.get(page_object.status, '操作')
                return CrudResponseModel(is_success=True, message=f'{action}成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入会议室 id 为空')

    @classmethod
    async def meeting_room_detail_services(cls, query_db: AsyncSession, room_id: int) -> MeetingRoomPageQueryModel:
        """
        获取会议室详细信息 service
        """
        room = await MeetingRoomDao.get_meeting_room_detail_by_id(query_db, room_id)
        result = MeetingRoomPageQueryModel(**CamelCaseUtil.transform_result(room)) if room else MeetingRoomPageQueryModel()
        return result


class MeetingOrderService:
    """
    会议室预定服务层
    """

    @classmethod
    async def get_meeting_order_list_services(
            cls, query_db: AsyncSession, query_object: MeetingOrderPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取预定列表信息 service
        """
        order_list_result = await MeetingOrderDao.get_meeting_order_list(query_db, query_object, is_page)
        return CamelCaseUtil.transform_result(order_list_result)

    @classmethod
    async def add_meeting_order_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddMeetingOrderModel
    ) -> CrudResponseModel:
        """
        新增预定信息 service
        """
        try:
            # 验证结束时间大于开始时间
            if page_object.end_date and page_object.start_date:
                if page_object.end_date <= page_object.start_date:
                    raise ServiceException(message='结束时间需要大于开始时间')

            # 检查同一会议室在相同时间段内是否存在相同主题的预定记录（排除待审核和已拒绝的记录）
            duplicate_check = await MeetingOrderDao.check_duplicate_order(
                query_db,
                page_object.room_id,
                page_object.title,
                page_object.start_date,
                page_object.end_date
            )

            if duplicate_check > 0:
                raise ServiceException(message='该会议室在此时间段已有相同主题的预定记录，请勿重复提交')

            # 检查时间冲突（同一会议室在同一时间段内的任何预定）
            conflict_count = await MeetingOrderDao.check_time_conflict(
                query_db,
                page_object.room_id,
                page_object.start_date,
                page_object.end_date
            )

            if conflict_count > 0:
                raise ServiceException(message='您所选的时间区间已有预定记录，请重新选时间')

            current_time = int(datetime.now().timestamp())
            order_data = page_object.model_dump(exclude_unset=True)
            order_data['create_time'] = current_time
            order_data['update_time'] = current_time
            order_data['delete_time'] = 0
            order_data['check_status'] = 1  # 待审核

            await MeetingOrderDao.add_meeting_order_dao(query_db, order_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_meeting_order_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditMeetingOrderModel
    ) -> CrudResponseModel:
        """
        编辑预定信息 service
        """
        # 验证结束时间大于开始时间
        if page_object.end_date and page_object.start_date:
            if page_object.end_date <= page_object.start_date:
                raise ServiceException(message='结束时间需要大于开始时间')

        # 检查时间冲突（排除当前记录）
        conflict_count = await MeetingOrderDao.check_time_conflict(
            query_db,
            page_object.room_id,
            page_object.start_date,
            page_object.end_date,
            page_object.id
        )

        if conflict_count > 0:
            raise ServiceException(message='您所选的时间区间已有预定记录，请重新选时间')

        order_data = page_object.model_dump(exclude_unset=True)
        order_info = await cls.meeting_order_detail_services(query_db, page_object.id)

        if order_info.id:
            try:
                order_data['update_time'] = int(datetime.now().timestamp())
                await MeetingOrderDao.edit_meeting_order_dao(query_db, order_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='预定记录不存在')

    @classmethod
    async def delete_meeting_order_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteMeetingOrderModel
    ) -> CrudResponseModel:
        """
        删除预定信息 service
        """
        if page_object.id:
            try:
                order = await cls.meeting_order_detail_services(query_db, page_object.id)
                if not order.id:
                    raise ServiceException(message='预定记录不存在')

                await MeetingOrderDao.delete_meeting_order_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入预定记录 id 为空')

    @classmethod
    async def meeting_order_detail_services(cls, query_db: AsyncSession, order_id: int) -> MeetingOrderPageQueryModel:
        """
        获取预定详细信息 service
        """
        order = await MeetingOrderDao.get_meeting_order_detail_by_id(query_db, order_id)
        result = MeetingOrderPageQueryModel(**CamelCaseUtil.transform_result(order)) if order else MeetingOrderPageQueryModel()
        return result


class MeetingRecordsService:
    """
    会议纪要服务层
    """

    @classmethod
    async def get_meeting_records_list_services(
            cls, query_db: AsyncSession, query_object: MeetingRecordsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取会议纪要列表信息 service
        """
        records_list_result = await MeetingRecordsDao.get_meeting_records_list(query_db, query_object, is_page)
        
        if isinstance(records_list_result, PageModel):
            formatted_rows = []
            for row in records_list_result.rows:
                if isinstance(row, (list, tuple)) and len(row) >= 1:
                    record_obj = row[0]
                    extra_fields = list(row[1:]) if len(row) > 1 else []
                    
                    record_dict = CamelCaseUtil.transform_result(record_obj)
                    
                    if isinstance(record_dict, dict):
                        create_time = record_dict.get('createTime')
                        if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                            try:
                                if create_time > 1e12:
                                    create_time_seconds = create_time / 1000
                                else:
                                    create_time_seconds = create_time
                                record_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"创建时间格式化失败: {create_time}, 错误: {e}")
                                record_dict['createTime'] = ''
                        else:
                            record_dict['createTime'] = ''
                        
                        update_time = record_dict.get('updateTime')
                        if update_time and isinstance(update_time, (int, float)) and update_time > 0:
                            try:
                                if update_time > 1e12:
                                    update_time_seconds = update_time / 1000
                                else:
                                    update_time_seconds = update_time
                                record_dict['updateTime'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"更新时间格式化失败: {update_time}, 错误: {e}")
                                record_dict['updateTime'] = ''
                        else:
                            record_dict['updateTime'] = ''
                        
                        meeting_date = record_dict.get('meetingDate')
                        if meeting_date and isinstance(meeting_date, (int, float)) and meeting_date > 0:
                            try:
                                if meeting_date > 1e12:
                                    meeting_date_seconds = meeting_date / 1000
                                else:
                                    meeting_date_seconds = meeting_date
                                record_dict['meetingDate'] = datetime.fromtimestamp(meeting_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"会议时间格式化失败: {meeting_date}, 错误: {e}")
                                record_dict['meetingDate'] = ''
                        else:
                            record_dict['meetingDate'] = ''
                    
                    formatted_row = [record_dict] + extra_fields
                    formatted_rows.append(formatted_row)
            
            records_list_result.rows = formatted_rows
            return records_list_result
        elif isinstance(records_list_result, list):
            formatted_list = []
            for row in records_list_result:
                if isinstance(row, (list, tuple)) and len(row) >= 1:
                    record_obj = row[0]
                    extra_fields = list(row[1:]) if len(row) > 1 else []
                    
                    record_dict = CamelCaseUtil.transform_result(record_obj)
                    
                    if isinstance(record_dict, dict):
                        create_time = record_dict.get('createTime')
                        if create_time and isinstance(create_time, (int, float)) and create_time > 0:
                            try:
                                if create_time > 1e12:
                                    create_time_seconds = create_time / 1000
                                else:
                                    create_time_seconds = create_time
                                record_dict['createTime'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"创建时间格式化失败: {create_time}, 错误: {e}")
                                record_dict['createTime'] = ''
                        else:
                            record_dict['createTime'] = ''
                        
                        update_time = record_dict.get('updateTime')
                        if update_time and isinstance(update_time, (int, float)) and update_time > 0:
                            try:
                                if update_time > 1e12:
                                    update_time_seconds = update_time / 1000
                                else:
                                    update_time_seconds = update_time
                                record_dict['updateTime'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"更新时间格式化失败: {update_time}, 错误: {e}")
                                record_dict['updateTime'] = ''
                        else:
                            record_dict['updateTime'] = ''
                        
                        meeting_date = record_dict.get('meetingDate')
                        if meeting_date and isinstance(meeting_date, (int, float)) and meeting_date > 0:
                            try:
                                if meeting_date > 1e12:
                                    meeting_date_seconds = meeting_date / 1000
                                else:
                                    meeting_date_seconds = meeting_date
                                record_dict['meetingDate'] = datetime.fromtimestamp(meeting_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logger.error(f"会议时间格式化失败: {meeting_date}, 错误: {e}")
                                record_dict['meetingDate'] = ''
                        else:
                            record_dict['meetingDate'] = ''
                    
                    formatted_row = [record_dict] + extra_fields
                    formatted_list.append(formatted_row)
            
            return formatted_list
        
        return CamelCaseUtil.transform_result(records_list_result)

    @classmethod
    async def add_meeting_records_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddMeetingRecordsModel
    ) -> CrudResponseModel:
        """
        新增会议纪要信息 service
        """
        try:
            # 检查是否存在重复的会议纪要（同一会议室、同一会议时间）
            duplicate_count = await MeetingRecordsDao.check_duplicate_records(
                query_db,
                page_object.room_id,
                page_object.meeting_date
            )

            if duplicate_count > 0:
                raise ServiceException(message='该会议室在此会议时间已有会议纪要记录，请勿重复提交')

            current_time = int(datetime.now().timestamp())
            records_data = page_object.model_dump(exclude_unset=True)
            records_data['create_time'] = current_time
            records_data['update_time'] = current_time
            records_data['delete_time'] = 0

            await MeetingRecordsDao.add_meeting_records_dao(query_db, records_data)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_meeting_records_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditMeetingRecordsModel
    ) -> CrudResponseModel:
        """
        编辑会议纪要信息 service
        """
        records_data = page_object.model_dump(exclude_unset=True)
        records_info = await cls.meeting_records_detail_services(query_db, page_object.id)

        if records_info.id:
            try:
                records_data['update_time'] = int(datetime.now().timestamp())
                await MeetingRecordsDao.edit_meeting_records_dao(query_db, records_data)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='会议纪要记录不存在')

    @classmethod
    async def delete_meeting_records_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteMeetingRecordsModel
    ) -> CrudResponseModel:
        """
        删除会议纪要信息 service
        """
        if page_object.id:
            try:
                records = await cls.meeting_records_detail_services(query_db, page_object.id)
                if not records.id:
                    raise ServiceException(message='会议纪要记录不存在')

                await MeetingRecordsDao.delete_meeting_records_dao(query_db, page_object.id)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入会议纪要记录 id 为空')



    @classmethod
    async def meeting_records_detail_services(cls, query_db: AsyncSession, records_id: int) -> MeetingRecordsPageQueryModel:
        """
        获取会议纪要详细信息 service
        """
        anchor_user = aliased(SysUser, name='anchor')
        recorder_user = aliased(SysUser, name='recorder')
        
        query = (
            select(OaMeetingRecords,
                   OaMeetingRoom.title.label('room_name'),
                   anchor_user.nick_name.label('anchor_name'),
                   recorder_user.nick_name.label('recorder_name'),
                   SysDept.dept_name.label('dept_name'))
            .join(OaMeetingRoom, OaMeetingRoom.id == OaMeetingRecords.room_id, isouter=True)
            .join(anchor_user, anchor_user.user_id == OaMeetingRecords.anchor_id, isouter=True)
            .join(recorder_user, recorder_user.user_id == OaMeetingRecords.recorder_id, isouter=True)
            .join(SysDept, SysDept.dept_id == OaMeetingRecords.did, isouter=True)
            .where(OaMeetingRecords.id == records_id)
        )
        
        result = await query_db.execute(query)
        row = result.first()
        
        if not row:
            return MeetingRecordsPageQueryModel()
        
        records_obj = row[0]
        room_name = row[1]
        anchor_name = row[2]
        recorder_name = row[3]
        dept_name = row[4]
        
        # 转换为字典
        records_dict = CamelCaseUtil.transform_result(records_obj)
        
        # 添加关联字段
        records_dict['roomName'] = room_name
        records_dict['anchorName'] = anchor_name
        records_dict['recorderName'] = recorder_name
        records_dict['deptName'] = dept_name
        
        # 格式化时间字段（添加新的字符串字段，不覆盖原始时间戳）
        meeting_date = records_dict.get('meetingDate')
        if meeting_date and isinstance(meeting_date, (int, float)) and meeting_date > 0:
            try:
                if meeting_date > 1e12:
                    meeting_date_seconds = meeting_date / 1000
                else:
                    meeting_date_seconds = meeting_date
                records_dict['meetingDateStr'] = datetime.fromtimestamp(meeting_date_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"会议时间格式化失败: {meeting_date}, 错误: {e}")
                records_dict['meetingDateStr'] = ''
        else:
            records_dict['meetingDateStr'] = ''
        
        create_time = records_dict.get('createTime')
        if create_time and isinstance(create_time, (int, float)) and create_time > 0:
            try:
                if create_time > 1e12:
                    create_time_seconds = create_time / 1000
                else:
                    create_time_seconds = create_time
                records_dict['createTimeStr'] = datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"创建时间格式化失败: {create_time}, 错误: {e}")
                records_dict['createTimeStr'] = ''
        else:
            records_dict['createTimeStr'] = ''
        
        update_time = records_dict.get('updateTime')
        if update_time and isinstance(update_time, (int, float)) and update_time > 0:
            try:
                if update_time > 1e12:
                    update_time_seconds = update_time / 1000
                else:
                    update_time_seconds = update_time
                records_dict['updateTimeStr'] = datetime.fromtimestamp(update_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.error(f"更新时间格式化失败: {update_time}, 错误: {e}")
                records_dict['updateTimeStr'] = ''
        else:
            records_dict['updateTimeStr'] = ''
        
        result = MeetingRecordsPageQueryModel(**records_dict)
        return result