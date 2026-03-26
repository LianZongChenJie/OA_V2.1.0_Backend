from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.meeting_dao import MeetingRoomDao, MeetingOrderDao, MeetingRecordsDao
from module_admin.entity.vo.meeting_vo import (
    MeetingRoomPageQueryModel,
    MeetingRoomModel,
    AddMeetingRoomModel,
    EditMeetingRoomModel,
    DeleteMeetingRoomModel,
    MeetingRoomStatusModel,
    MeetingOrderPageQueryModel,
    AddMeetingOrderModel,
    EditMeetingOrderModel,
    DeleteMeetingOrderModel,
    MeetingRecordsPageQueryModel,
    AddMeetingRecordsModel,
    EditMeetingRecordsModel,
    DeleteMeetingRecordsModel,
)
from utils.common_util import CamelCaseUtil


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
        records = await MeetingRecordsDao.get_meeting_records_detail_by_id(query_db, records_id)
        result = MeetingRecordsPageQueryModel(**CamelCaseUtil.transform_result(records)) if records else MeetingRecordsPageQueryModel()
        return result
