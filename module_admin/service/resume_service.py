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
    InterviewResultModel, ConfirmEntryModel, ResumeRecommendModel,
    AddEmailTemplateModel, EditEmailTemplateModel, DeleteEmailTemplateModel,
    EntryProjectModel, ResumeRecommendPageQueryModel
)
from exceptions.exception import ServiceException

logger = logging.getLogger(__name__)


class ResumeService:
    """
    简历库管理服务层
    """

    @staticmethod
    def _parse_entry_time(entry_time_str: str | None) -> int:
        """
        解析入职时间，支持多种格式：
        - 时间戳字符串（如 "1717920000"）
        - 日期字符串（如 "2026-06-15"）
        - 日期时间字符串（如 "2026-06-15 10:30:00"）
        """
        if not entry_time_str:
            return int(datetime.now().timestamp())
        
        # 尝试作为整数时间戳解析
        try:
            return int(entry_time_str)
        except ValueError:
            pass
        
        # 尝试作为日期字符串解析
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
            try:
                dt = datetime.strptime(entry_time_str, fmt)
                return int(dt.timestamp())
            except ValueError:
                continue
        
        # 如果都解析失败，返回当前时间戳
        return int(datetime.now().timestamp())

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
        # 身份证号唯一性校验
        if page_object.idcard and page_object.idcard.strip():
            existing_resume = await ResumeDao.get_resume_by_idcard(query_db, page_object.idcard.strip())
            if existing_resume:
                raise ServiceException(message=f'身份证号已存在：{page_object.idcard}')

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
        except ServiceException:
            raise
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增失败：{str(e)}') from e

    @classmethod
    async def release_resume_services(cls, query_db: AsyncSession, resume_id: int, status: str = '5') -> CrudResponseModel:
        """释放简历"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{resume_id}')

        try:
            await ResumeDao.release_resume_dao(query_db, resume_id, status)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='释放成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'释放失败：{str(e)}') from e

    @classmethod
    async def edit_resume_services(cls, query_db: AsyncSession, page_object: EditResumeModel) -> CrudResponseModel:
        """编辑简历"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.id}')

        # 身份证号唯一性校验（排除当前简历）
        if page_object.idcard and page_object.idcard.strip():
            existing_resume = await ResumeDao.get_resume_by_idcard(query_db, page_object.idcard.strip())
            if existing_resume and existing_resume.id != page_object.id:
                raise ServiceException(message=f'身份证号已存在：{page_object.idcard}')

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

        # 直接使用传入的 status 值，不进行转换
        result = str(page_object.status)

        try:
            await ResumeDao.update_resume_status_dao(query_db, page_object.resume_id, result)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message=f'状态已更新为{result}')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'更新状态失败：{str(e)}') from e

    @classmethod
    async def confirm_entry_services(cls, query_db: AsyncSession, page_object: ConfirmEntryModel) -> CrudResponseModel:
        """确认入职"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.resume_id}')

        # 检查状态是否允许入职
        if resume_info.status != '2':
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
                graduate_school=resume_info.graduate_school or '',
                education=resume_info.education or '',
                age=resume_info.age,
                entry_time=cls._parse_entry_time(page_object.entry_time),
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

    @classmethod
    async def recommend_resume_services(cls, query_db: AsyncSession, page_object: ResumeRecommendModel) -> CrudResponseModel:
        """推荐简历到项目/客户"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.resume_id}')

        # 检查状态是否允许推荐，只有状态为 [0, 3, 5] 时允许推荐
        # 0: 初始状态, 3: 未通过, 5: 已释放
        allowed_status = ['0', '3', '5']
        if resume_info.status not in allowed_status:
            raise ServiceException(message=f'当前状态为{resume_info.status}，不允许推荐')

        # 项目不再是必填项，如果有项目ID则验证项目是否存在
        project_name = None
        if page_object.project_id:
            from module_project.dao.project_dao import ProjectDao
            project_info = await ProjectDao.get_project_detail_by_id(query_db, page_object.project_id)
            if not project_info:
                raise ServiceException(message=f'项目不存在，ID：{page_object.project_id}')
            project_name = project_info['project_info'].name

        # 客户ID也不是必填项，如果有客户ID可以记录（不需要验证，直接保存）

        try:
            await ResumeDao.recommend_resume_dao(
                query_db, 
                page_object, 
                project_name=project_name,
                customer_name=page_object.customer_name
            )
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='推荐成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'推荐失败：{str(e)}') from e

    @classmethod
    async def get_resume_recommend_list_services(
            cls, query_db: AsyncSession, query_object: ResumeRecommendPageQueryModel, is_page: bool = False
    ) -> dict | list:
        """获取简历推荐记录列表"""
        try:
            result, total = await ResumeDao.get_resume_recommend_list(query_db, query_object, is_page)
            if is_page:
                has_next = total > query_object.page_num * query_object.page_size
                return {
                    'rows': result,
                    'total': total,
                    'pageNum': query_object.page_num,
                    'pageSize': query_object.page_size,
                    'hasNext': has_next
                }
            return result
        except Exception as e:
            raise ServiceException(message=f'获取推荐记录失败：{str(e)}') from e

    @classmethod
    async def add_email_template_services(cls, query_db: AsyncSession, page_object: AddEmailTemplateModel) -> CrudResponseModel:
        """新增邮件模板"""
        try:
            await ResumeDao.add_email_template_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增失败：{str(e)}') from e

    @classmethod
    async def get_email_template_list_services(cls, query_db: AsyncSession, page_num: int = 1, page_size: int = 10) -> dict:
        """获取邮件模板列表（分页）"""
        try:
            result = await ResumeDao.get_email_template_list(query_db, page_num, page_size)
            return result
        except Exception as e:
            raise ServiceException(message=f'获取模板列表失败：{str(e)}') from e

    @classmethod
    async def get_email_template_detail_services(cls, query_db: AsyncSession, template_id: int) -> dict:
        """获取邮件模板详情"""
        template_info = await ResumeDao.get_email_template_by_id(query_db, template_id)
        if not template_info:
            raise ServiceException(message=f'模板不存在，ID：{template_id}')
        return template_info

    @classmethod
    async def edit_email_template_services(cls, query_db: AsyncSession, page_object: EditEmailTemplateModel) -> CrudResponseModel:
        """编辑邮件模板"""
        template_info = await ResumeDao.get_email_template_by_id(query_db, page_object.id)
        if not template_info:
            raise ServiceException(message=f'模板不存在，ID：{page_object.id}')

        try:
            await ResumeDao.edit_email_template_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'修改失败：{str(e)}') from e

    @classmethod
    async def delete_email_template_services(cls, query_db: AsyncSession, page_object: DeleteEmailTemplateModel) -> CrudResponseModel:
        """删除邮件模板"""
        if not page_object.ids:
            raise ServiceException(message='传入模板ID为空')

        try:
            template_ids = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]
            if not template_ids:
                raise ServiceException(message='模板ID格式错误，应为数字，多个用逗号分隔')

            await ResumeDao.delete_email_template_dao(query_db, template_ids)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ValueError:
            raise ServiceException(message='模板ID必须为数字，多个用逗号分隔')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除失败：{str(e)}') from e

    @classmethod
    async def entry_project_services(cls, query_db: AsyncSession, page_object: EntryProjectModel) -> CrudResponseModel:
        """入场项目"""
        resume_info = await ResumeDao.get_resume_detail_by_id(query_db, page_object.resume_id)
        if not resume_info:
            raise ServiceException(message=f'简历信息不存在，ID：{page_object.resume_id}')

        # 检查状态是否允许入场
        if resume_info.status not in ['2', '4']:  # 2已通过, 4已入职
            raise ServiceException(message=f'当前状态为{resume_info.status}，只有已通过或已入职状态才能入场')

        # 获取项目信息
        from module_project.dao.project_dao import ProjectDao
        project_info = await ProjectDao.get_project_detail_by_id(query_db, page_object.project_id)
        if not project_info:
            raise ServiceException(message=f'项目不存在，ID：{page_object.project_id}')

        try:
            await ResumeDao.entry_project_dao(query_db, page_object.resume_id, page_object.project_id, project_info['project_info'].name)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='入场成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'入场失败：{str(e)}') from e