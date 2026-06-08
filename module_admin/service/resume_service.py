import logging
from datetime import datetime
from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from module_admin.dao.resume_dao import ResumeDao
from module_admin.dao.user_dao import UserDao
from module_admin.entity.do.user_do import SysUser, SysUserRole
from module_admin.entity.vo.resume_vo import (
    ResumePageQueryModel, AddResumeModel, EditResumeModel, DeleteResumeModel,
    InterviewResultModel, ConfirmEntryModel
)
from exceptions.exception import ServiceException

logger = logging.getLogger(__name__)


class ResumeService:
    """
    简历库管理服务层
    """

    @classmethod
    async def get_resume_list_services(
            cls, query_db: AsyncSession, query_object: ResumePageQueryModel, is_page: bool = False
    ) -> dict | list:
        """获取简历列表"""
        try:
            result, total = await ResumeDao.get_resume_list(query_db, query_object, is_page)
            if is_page:
                has_next = total > query_object.page_num * query_object.page_size
                # 直接返回字典，使用驼峰命名
                return {
                    'rows': result,
                    'total': total,
                    'pageNum': query_object.page_num,
                    'pageSize': query_object.page_size,
                    'hasNext': has_next
                }
            return result
        except Exception as e:
            logger.error(f'获取简历列表失败：{str(e)}', exc_info=True)
            raise ServiceException(message=f'获取简历列表失败：{str(e)}') from e

    @classmethod
    async def resume_detail_services(cls, query_db: AsyncSession, resume_id: int) -> dict:
        """获取简历详情"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{resume_id}')

        try:
            attachments = await ResumeDao.get_resume_attachments(query_db, resume_id)
            return {'resume': resume_info, 'attachments': attachments}
        except Exception as e:
            raise ServiceException(message=f'获取简历附件失败：{str(e)}') from e

    @classmethod
    async def add_resume_services(cls, query_db: AsyncSession, page_object: AddResumeModel) -> CrudResponseModel:
        """新增简历"""
        try:
            # 保存简历基本信息
            resume_result = await ResumeDao.add_resume_dao(query_db, page_object)
            resume_id = resume_result.id

            # 如果有附件，保存附件
            if page_object.attachments and len(page_object.attachments) > 0:
                for attachment in page_object.attachments:
                    await ResumeDao.add_resume_attachment_dao(query_db, resume_id, attachment)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功', result={'resume_id': resume_id})
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增失败：{str(e)}') from e

    @classmethod
    async def edit_resume_services(cls, query_db: AsyncSession, page_object: EditResumeModel) -> CrudResponseModel:
        """编辑简历"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.id}')

        try:
            # 更新简历基本信息
            await ResumeDao.edit_resume_dao(query_db, page_object)

            # 删除原有附件（软删除）
            existing_attachments = await ResumeDao.get_resume_attachments(query_db, page_object.id)
            if existing_attachments:
                attachment_ids = [att.id for att in existing_attachments]
                delete_time = int(datetime.now().timestamp())
                await ResumeDao.batch_delete_tender_attachments_dao(query_db, attachment_ids, delete_time)

            # 如果有新附件，新增附件
            if page_object.attachments and len(page_object.attachments) > 0:
                for attachment in page_object.attachments:
                    await ResumeDao.add_resume_attachment_dao(query_db, page_object.id, attachment)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'修改失败：{str(e)}') from e

    @classmethod
    async def delete_resume_services(cls, query_db: AsyncSession, page_object: DeleteResumeModel) -> CrudResponseModel:
        """删除简历（软删除）"""
        if not page_object.ids:
            raise ServiceException(message='传入简历ID为空')

        try:
            resume_ids = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]
            if not resume_ids:
                raise ServiceException(message='简历ID格式错误，应为数字，多个用逗号分隔')

            delete_time = int(datetime.now().timestamp())
            await ResumeDao.delete_resume_dao(query_db, resume_ids, delete_time)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ValueError:
            raise ServiceException(message='简历ID必须为数字，多个用逗号分隔')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除失败：{str(e)}') from e

    @classmethod
    async def interview_result_services(cls, query_db: AsyncSession, page_object: InterviewResultModel) -> CrudResponseModel:
        """面试结果处理"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.resume_id}')

        # 检查状态是否允许更新
        if resume_info.status in ['已入职', '已释放']:
            raise ServiceException(message=f'当前状态为{resume_info.status}，不允许修改面试结果')

        try:
            await ResumeDao.update_resume_status_dao(query_db, page_object.resume_id, page_object.result)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message=f'面试结果已更新为{page_object.result}')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'更新面试结果失败：{str(e)}') from e

    @classmethod
    async def confirm_entry_services(cls, query_db: AsyncSession, page_object: ConfirmEntryModel) -> CrudResponseModel:
        """确认入职"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.resume_id}')

        # 检查状态是否允许入职
        if resume_info.status != '已通过':
            raise ServiceException(message=f'当前状态为{resume_info.status}，只有已通过状态才能办理入职')

        # 检查登录账号是否已存在
        existing_user = await UserDao.get_user_by_name(query_db, page_object.user_name)
        if existing_user:
            raise ServiceException(message=f'登录账号已存在：{page_object.user_name}')

        try:
            # 创建用户
            user_info = SysUser(
                dept_id=page_object.dept_id,
                did=page_object.post_id,
                pid=page_object.dept_id,
                position_id=page_object.position_id,
                position_name=0,
                position_rank=0,
                user_name=page_object.user_name,
                nick_name=page_object.nick_name or resume_info.name,
                user_type=page_object.user_type or '01',
                is_staff=page_object.is_staff or 1,
                email=page_object.email or resume_info.email or '',
                phonenumber=resume_info.phone,
                idcard=resume_info.idcard or '',
                sex=resume_info.sex or '0',
                password=page_object.password,  # 注意：实际项目中需要加密存储
                status='0',
                del_flag='0',
                admin_status=1,  # 正常状态
                city=resume_info.city or '',
                entry_time=page_object.entry_time or int(datetime.now().timestamp()),
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            query_db.add(user_info)
            await query_db.flush()
            user_id = user_info.user_id

            # 关联角色
            for role_id in page_object.role_ids:
                user_role = SysUserRole(user_id=user_id, role_id=role_id)
                query_db.add(user_role)

            # 更新简历状态为已入职，并关联用户ID
            await ResumeDao.update_resume_user_id_dao(query_db, page_object.resume_id, user_id)

            await query_db.commit()
            return CrudResponseModel(is_success=True, message='入职办理成功', result={'user_id': user_id})
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'入职办理失败：{str(e)}') from e