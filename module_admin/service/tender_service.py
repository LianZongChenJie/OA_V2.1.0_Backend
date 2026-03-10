from typing import Any
from datetime import datetime  # 新增导入

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel, CrudResponseModel
from module_admin.dao.tender_dao import TenderDao
from module_admin.entity.vo.tender_vo import (
    TenderPageQueryModel,
    AddTenderModel,
    EditTenderModel,
    DeleteTenderModel,
    AddTenderAttachmentModel,
    DeleteTenderAttachmentModel,
)
from exceptions.exception import ServiceException


class TenderService:
    """
    招投标管理服务层
    """

    @classmethod
    async def get_tender_list_services(
            cls, query_db: AsyncSession, query_object: TenderPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取投标信息列表 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 投标信息列表对象
        """
        tender_list_result = await TenderDao.get_tender_list(query_db, query_object, is_page)
        return tender_list_result

    @classmethod
    async def tender_detail_services(cls, query_db: AsyncSession, tender_id: int) -> dict[str, Any]:
        """
        获取投标信息详情 service

        :param query_db: orm 对象
        :param tender_id: 投标 ID
        :return: 投标详情信息
        """
        tender_info = await TenderDao.get_tender_detail_by_id(query_db, tender_id)
        if not tender_info:
            raise ServiceException(message='投标信息不存在')

        # 获取附件列表
        attachments = await TenderDao.get_tender_attachments(query_db, tender_id)

        return {
            'tender': tender_info,
            'attachments': attachments
        }

    @classmethod
    async def add_tender_services(cls, query_db: AsyncSession, page_object: AddTenderModel) -> CrudResponseModel:
        """
        新增投标信息 service
        """
        # 1. 日期格式转换
        if page_object.purchase_date:
            try:
                dt = datetime.strptime(page_object.purchase_date, '%Y-%m-%d')
                page_object.purchase_date = dt.date()
            except ValueError:
                raise ServiceException(message='purchase_date 日期格式错误，仅支持 YYYY-MM-DD')
        if page_object.bid_opening_date:
            try:
                dt = datetime.strptime(page_object.bid_opening_date, '%Y-%m-%d')
                page_object.bid_opening_date = dt.date()
            except ValueError:
                raise ServiceException(message='bid_opening_date 日期格式错误，仅支持 YYYY-MM-DD')

        # 2. 强制转换枚举字段为中文（终极版：不管传入什么，直接覆盖）
        # 先把对象转成字典，避免属性赋值失效
        tender_dict = page_object.model_dump()

        # 强制替换枚举字段值
        enum_mapping = {
            'is_tender_submitted': '是' if tender_dict.get('is_tender_submitted') in ['是', 'YES', 'yes'] else '否',
            'has_tender_invoice': '是' if tender_dict.get('has_tender_invoice') in ['是', 'YES', 'yes'] else '否',
            'is_deposit_paid': '是' if tender_dict.get('is_deposit_paid') in ['是', 'YES', 'yes'] else '否',
            'is_deposit_refunded': '是' if tender_dict.get('is_deposit_refunded') in ['是', 'YES', 'yes'] else '否'
        }

        # 重新赋值给page_object
        for field, value in enum_mapping.items():
            setattr(page_object, field, value)

        try:
            await TenderDao.add_tender_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增失败，详细错误信息：{e}') from e

    @classmethod
    async def edit_tender_services(cls, query_db: AsyncSession, page_object: EditTenderModel) -> CrudResponseModel:
        """
        编辑投标信息 service

        :param query_db: orm 对象
        :param page_object: 编辑投标对象
        :return: 编辑投标校验结果
        """
        tender_info = await TenderDao.get_tender_detail_by_id(query_db, page_object.id)
        if not tender_info:
            raise ServiceException(message='投标信息不存在')

        try:
            await TenderDao.edit_tender_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'修改失败，详细错误信息：{e}') from e



    @classmethod
    async def delete_tender_services(
            cls, query_db: AsyncSession, page_object: DeleteTenderModel
    ) -> CrudResponseModel:
        """
        删除投标信息 service（软删除）
        """
        if not page_object.ids:
            raise ServiceException(message='传入投标 id 为空')

        try:
            # 拆分ID列表
            tender_ids = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]
            if not tender_ids:
                raise ServiceException(message='投标ID格式错误，应为数字，多个用逗号分隔')

            # 生成当前时间戳作为 delete_time
            delete_time = int(datetime.now().timestamp())

            # 调用 DAO（注意：DAO 是 @classmethod，需要用 cls 调用）
            await TenderDao.delete_tender_dao(query_db, tender_ids, delete_time)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ValueError:
            raise ServiceException(message='投标ID必须为数字，多个用逗号分隔')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除失败，详细错误信息：{e}') from e


    @classmethod
    async def add_tender_attachment_services(
            cls, query_db: AsyncSession, page_object: AddTenderAttachmentModel
    ) -> CrudResponseModel:
        """
        新增投标附件 service

        :param query_db: orm 对象
        :param page_object: 新增附件对象
        :return: 新增附件校验结果
        """
        # 验证投标记录是否存在
        tender_info = await TenderDao.get_tender_detail_by_id(query_db, page_object.project_tender_id)
        if not tender_info:
            raise ServiceException(message='关联的投标信息不存在')

        try:
            await TenderDao.add_tender_attachment_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增附件成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增附件失败，详细错误信息：{e}') from e

    @classmethod
    async def delete_tender_attachment_services(
            cls, query_db: AsyncSession, page_object: DeleteTenderAttachmentModel
    ) -> CrudResponseModel:
        """
        删除投标附件 service

        :param query_db: orm 对象
        :param page_object: 删除附件对象
        :return: 删除附件校验结果
        """
        if not page_object.ids:
            raise ServiceException(message='传入附件 id 为空')

        try:
            await TenderDao.delete_tender_attachment_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除附件成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除附件失败，详细错误信息：{e}') from e