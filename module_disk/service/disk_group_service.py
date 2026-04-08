"""
网盘分享空间管理服务层
"""
import time

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_disk.dao.disk_group_dao import DiskGroupDao
from module_disk.entity.do.disk_group_do import OaDiskGroup
from module_disk.entity.vo.disk_group_vo import (
    AddDiskGroupModel,
    DeleteDiskGroupModel,
    DiskGroupModel,
    DiskGroupPageQueryModel,
    EditDiskGroupModel,
)
from utils.log_util import logger


class DiskGroupService:
    """
    网盘分享空间管理服务层
    """

    @classmethod
    async def get_disk_group_list_services(
            cls, query_db: AsyncSession, query_object: DiskGroupPageQueryModel,
            where_conditions: list, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        获取网盘分享空间列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param where_conditions: 查询条件列表
        :param is_page: 是否开启分页
        :return: 分享空间列表信息对象
        """
        group_list_result = await DiskGroupDao.get_disk_group_list(
            query_db, query_object, where_conditions, is_page
        )

        return group_list_result

    @classmethod
    async def check_group_title_unique_services(
            cls, query_db: AsyncSession, page_object: DiskGroupModel
    ) -> bool:
        """
        校验分享空间名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 分享空间对象
        :return: 校验结果
        """
        exclude_id = page_object.id if page_object.id else None
        group = await DiskGroupDao.get_disk_group_by_title(
            query_db, page_object.title, exclude_id
        )
        return group is None

    @classmethod
    async def add_disk_group_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddDiskGroupModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        新增网盘分享空间 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增分享空间对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增分享空间校验结果
        """
        if page_object.title in ['全部', '未共享空间']:
            raise ServiceException(message='该共享空间名称已经存在')

        if not await cls.check_group_title_unique_services(query_db, page_object):
            raise ServiceException(message='该共享空间名称已经被其他员工占用')

        try:
            current_time = int(time.time())

            add_group = OaDiskGroup(
                title=page_object.title,
                admin_id=current_user_id,
                director_uids=page_object.director_uids if page_object.director_uids else '',
                group_uids=page_object.group_uids if page_object.group_uids else '',
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )

            await DiskGroupDao.add_disk_group_dao(query_db, add_group)
            await query_db.flush()
            logger.info(f'新增网盘分享空间成功，ID: {add_group.id}, 名称: {add_group.title}')
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='添加成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增网盘分享空间失败: {str(e)}')
            raise e

    @classmethod
    async def edit_disk_group_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditDiskGroupModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        编辑网盘分享空间 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑分享空间对象
        :param current_user_id: 当前登录用户 ID
        :return: 编辑分享空间校验结果
        """
        if page_object.title in ['全部', '未共享空间']:
            raise ServiceException(message='该共享空间名称已经存在')

        group_detail = await DiskGroupDao.get_disk_group_detail_by_id(query_db, page_object.id)
        if not group_detail:
            raise ServiceException(message='分享空间不存在')

        if current_user_id != 1 and group_detail.admin_id != current_user_id:
            raise ServiceException(message='只有超级管理员和创建人才有权限操作')

        if not await cls.check_group_title_unique_services(query_db, page_object):
            raise ServiceException(message='该共享空间名称已经被其他员工占用')

        try:
            update_time = int(time.time())

            update_data = {
                'title': page_object.title,
                'director_uids': page_object.director_uids if page_object.director_uids else '',
                'group_uids': page_object.group_uids if page_object.group_uids else '',
                'update_time': update_time
            }

            await DiskGroupDao.edit_disk_group_dao(query_db, page_object.id, update_data)
            await query_db.commit()
            logger.info(f'编辑网盘分享空间成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'编辑网盘分享空间失败: {str(e)}')
            raise e

    @classmethod
    async def delete_disk_group_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteDiskGroupModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        删除网盘分享空间 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除分享空间对象
        :param current_user_id: 当前登录用户 ID
        :return: 删除分享空间校验结果
        """
        group_detail = await DiskGroupDao.get_disk_group_detail_by_id(query_db, page_object.id)
        if not group_detail:
            raise ServiceException(message='分享空间不存在')

        if current_user_id != 1 and group_detail.admin_id != current_user_id:
            raise ServiceException(message='只有超级管理员和创建人才有权限操作')

        disk_count = await DiskGroupDao.get_group_disk_count(query_db, page_object.id)
        if disk_count > 0:
            raise ServiceException(message='该共享空间还存在文件，请去除文件或者转移文件后再删除')

        try:
            await DiskGroupDao.delete_disk_group_dao(query_db, page_object.id)
            await query_db.commit()
            logger.info(f'删除网盘分享空间成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'删除网盘分享空间失败: {str(e)}')
            raise e

    @classmethod
    async def disk_group_detail_services(cls, query_db: AsyncSession, group_id: int) -> DiskGroupModel:
        """
        获取网盘分享空间详细信息 service

        :param query_db: orm 对象
        :param group_id: 分享空间 id
        :return: 分享空间 id 对应的信息
        """
        group = await DiskGroupDao.get_disk_group_detail_by_id(query_db, group_id)

        if not group:
            return DiskGroupModel()

        group_dict = {
            'id': group.id,
            'title': group.title,
            'admin_id': group.admin_id,
            'director_uids': group.director_uids,
            'group_uids': group.group_uids,
            'create_time': group.create_time,
            'update_time': group.update_time,
            'delete_time': group.delete_time,
        }

        result = DiskGroupModel(**group_dict)
        return result
