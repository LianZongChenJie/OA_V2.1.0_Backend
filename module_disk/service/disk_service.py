"""
网盘文件管理服务层
"""
import time
from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_disk.dao.disk_dao import DiskDao
from module_disk.entity.do.disk_do import OaDisk
from module_disk.entity.vo.disk_vo import (
    AddDiskModel,
    BackDiskModel,
    ClearDiskModel,
    DeleteDiskModel,
    DiskModel,
    DiskPageQueryModel,
    EditDiskModel,
    MoveDiskModel,
    StarDiskModel,
    UnstarDiskModel,
)
from utils.log_util import logger


class DiskService:
    """
    网盘文件管理服务层
    """

    @classmethod
    async def get_disk_list_services(
            cls, query_db: AsyncSession, query_object: DiskPageQueryModel,
            user_id: int, where_conditions: list, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取网盘文件列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :param where_conditions: 查询条件列表
        :param is_page: 是否开启分页
        :return: 网盘文件列表信息对象
        """
        disk_list_result = await DiskDao.get_disk_list(
            query_db, query_object, where_conditions, is_page
        )

        return disk_list_result

    @classmethod
    async def build_query_conditions(
            cls, query_object: DiskPageQueryModel, user_id: int, pid: int = 0,
            group_id: int = 0, is_star_filter: bool = False, ext_filter: str = None
    ) -> list:
        """
        构建查询条件

        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :param pid: 父文件夹ID
        :param group_id: 分享空间ID
        :param is_star_filter: 是否标星筛选
        :param ext_filter: 文件扩展名筛选
        :return: 查询条件列表
        """
        from sqlalchemy import or_

        conditions = []
        conditions.append(OaDisk.delete_time == 0)
        
        # 权限控制：只查询当前用户创建的文件（可选，根据业务需求决定是否需要）
        # conditions.append(OaDisk.admin_id == user_id)

        # group_id 筛选：如果指定了 group_id 则按 group_id 查询，否则不限制
        if group_id and group_id > 0:
            conditions.append(OaDisk.group_id == group_id)

        # 标星筛选
        if is_star_filter:
            conditions.append(OaDisk.types < 2)
            conditions.append(OaDisk.is_star == 1)
        # 文件扩展名筛选
        elif ext_filter:
            ext_list = [ext.strip() for ext in ext_filter.split(',') if ext.strip()]
            if ext_list:
                conditions.append(OaDisk.file_ext.in_(ext_list))
        # 默认按 pid 查询
        else:
            conditions.append(OaDisk.pid == pid)

        # 关键字搜索
        if query_object.keywords:
            conditions.append(OaDisk.name.like(f'%{query_object.keywords}%'))

        return conditions

    @classmethod
    async def build_clearlist_query_conditions(
            cls, query_object: DiskPageQueryModel, user_id: int, pid: int = 0, ext_filter: str = None
    ) -> list:
        """
        构建回收站查询条件

        :param query_object: 查询参数对象
        :param user_id: 当前用户ID
        :param pid: 父文件夹ID
        :param ext_filter: 文件扩展名筛选
        :return: 查询条件列表
        """
        conditions = []
        conditions.append(OaDisk.admin_id == user_id)
        conditions.append(OaDisk.clear_time == 0)
        
        # 如果 pid > 0，查询指定文件夹下的已删除文件
        # 如果 pid = 0，查询所有已删除的文件（delete_time > 0）
        if pid > 0:
            conditions.append(OaDisk.pid == pid)
        else:
            conditions.append(OaDisk.delete_time > 0)

        # 文件扩展名筛选
        if ext_filter:
            ext_list = [ext.strip() for ext in ext_filter.split(',') if ext.strip()]
            if ext_list:
                conditions.append(OaDisk.file_ext.in_(ext_list))

        # 关键字搜索
        if query_object.keywords:
            conditions.append(OaDisk.name.like(f'%{query_object.keywords}%'))

        return conditions

    @classmethod
    async def add_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddDiskModel,
            current_user_id: int, did: int = 0
    ) -> CrudResponseModel:
        """
        新增网盘文件信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增文件对象
        :param current_user_id: 当前登录用户 ID
        :param did: 部门ID
        :return: 新增文件校验结果
        """
        try:
            current_time = int(time.time())

            add_disk = OaDisk(
                pid=page_object.pid if page_object.pid else 0,
                did=did,
                types=page_object.types if page_object.types else 0,
                action_id=page_object.action_id if page_object.action_id else 0,
                group_id=page_object.group_id if page_object.group_id else 0,
                name=page_object.name,
                file_ext=page_object.file_ext if page_object.file_ext else '',
                file_size=page_object.file_size if page_object.file_size else 0,
                is_star=page_object.is_star if page_object.is_star else 0,
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time,
                delete_time=0,
                clear_time=0
            )

            await DiskDao.add_disk_dao(query_db, add_disk)
            await query_db.flush()
            logger.info(f'新增网盘文件成功，ID: {add_disk.id}, 名称: {add_disk.name}')
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'新增网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def edit_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditDiskModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        编辑网盘文件信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑文件对象
        :param current_user_id: 当前登录用户 ID
        :return: 编辑文件校验结果
        """
        disk_info = await cls.disk_detail_services(query_db, page_object.id)

        if not disk_info or not disk_info.id:
            raise ServiceException(message='文件不存在')

        if disk_info.admin_id != current_user_id and current_user_id != 1:
            raise ServiceException(message='只有超级管理员和创建人才有权限操作')

        try:
            update_time = int(time.time())

            update_data = {}
            if page_object.name is not None:
                update_data['name'] = page_object.name
            if page_object.update_time is not None:
                update_data['update_time'] = update_time

            await DiskDao.edit_disk_dao(query_db, page_object.id, update_data)
            await query_db.commit()
            logger.info(f'编辑网盘文件成功，ID: {page_object.id}')
            return CrudResponseModel(is_success=True, message='编辑成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'编辑网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def delete_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteDiskModel,
            current_user_id: int
    ) -> CrudResponseModel:
        """
        删除网盘文件信息 service（逻辑删除）

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除文件对象
        :param current_user_id: 当前登录用户 ID
        :return: 删除文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            update_list = []
            for disk_id in id_list:
                disk = await cls.disk_detail_services(query_db, disk_id)
                if not disk or not disk.id:
                    raise ServiceException(message=f'文件ID {disk_id} 不存在')

                if disk.admin_id != current_user_id and current_user_id != 1:
                    raise ServiceException(message=f'删除失败,【{disk.name}】不是你上传的文件')

                child_count = await DiskDao.get_child_disk_count(query_db, disk_id)
                if child_count > 0:
                    raise ServiceException(message=f'删除失败,请先清空【{disk.name}】里面的文件')

                update_list.append({
                    'id': disk_id,
                    'delete_time': int(time.time())
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'删除网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'删除网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def back_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: BackDiskModel
    ) -> CrudResponseModel:
        """
        恢复网盘文件 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 恢复文件对象
        :return: 恢复文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            update_list = []
            for disk_id in id_list:
                update_list.append({
                    'id': disk_id,
                    'delete_time': 0
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'恢复网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='恢复成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'恢复网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def clear_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: ClearDiskModel
    ) -> CrudResponseModel:
        """
        清除网盘文件 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 清除文件对象
        :return: 清除文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            update_list = []
            for disk_id in id_list:
                update_list.append({
                    'id': disk_id,
                    'clear_time': int(time.time())
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'清除网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='清除成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'清除网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def move_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: MoveDiskModel
    ) -> CrudResponseModel:
        """
        移动网盘文件 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 移动文件对象
        :return: 移动文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            parent_ids = await DiskDao.get_parent_ids(query_db, page_object.pid)

            update_list = []
            for disk_id in id_list:
                if disk_id in parent_ids or disk_id == page_object.pid:
                    disk = await cls.disk_detail_services(query_db, disk_id)
                    raise ServiceException(
                        message=f'移动失败,【{disk.name}】不能移动到文件夹本身或其子目录'
                    )

                update_list.append({
                    'id': disk_id,
                    'pid': page_object.pid,
                    'update_time': int(time.time())
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'移动网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='移动成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'移动网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def star_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: StarDiskModel
    ) -> CrudResponseModel:
        """
        标星网盘文件 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 标星文件对象
        :return: 标星文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            update_list = []
            for disk_id in id_list:
                update_list.append({
                    'id': disk_id,
                    'is_star': 1,
                    'update_time': int(time.time())
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'标星网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='标星成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'标星网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def unstar_disk_services(
            cls, request: Request, query_db: AsyncSession, page_object: UnstarDiskModel
    ) -> CrudResponseModel:
        """
        取消标星网盘文件 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 取消标星文件对象
        :return: 取消标星文件校验结果
        """
        id_list = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]

        try:
            update_list = []
            for disk_id in id_list:
                update_list.append({
                    'id': disk_id,
                    'is_star': 0,
                    'update_time': int(time.time())
                })

            await DiskDao.batch_update_disk_dao(query_db, update_list)
            await query_db.commit()
            logger.info(f'取消标星网盘文件成功，IDs: {page_object.ids}')
            return CrudResponseModel(is_success=True, message='取消标星成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'取消标星网盘文件失败: {str(e)}')
            raise e

    @classmethod
    async def disk_detail_services(cls, query_db: AsyncSession, disk_id: int) -> DiskModel:
        """
        获取网盘文件详细信息 service

        :param query_db: orm 对象
        :param disk_id: 文件 id
        :return: 文件 id 对应的信息
        """
        disk = await DiskDao.get_disk_detail_by_id(query_db, disk_id)

        if not disk:
            return DiskModel()

        disk_dict = {
            'id': disk.id,
            'pid': disk.pid,
            'did': disk.did,
            'types': disk.types,
            'action_id': disk.action_id,
            'group_id': disk.group_id,
            'name': disk.name,
            'file_ext': disk.file_ext,
            'file_size': disk.file_size,
            'is_star': disk.is_star,
            'admin_id': disk.admin_id,
            'create_time': disk.create_time,
            'update_time': disk.update_time,
            'delete_time': disk.delete_time,
            'clear_time': disk.clear_time,
        }

        result = DiskModel(**disk_dict)
        return result
