import logging
from typing import List
from datetime import datetime
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
import pandas as pd
from openpyxl.styles import PatternFill, Font

from common.vo import PageModel, CrudResponseModel
from module_admin.dao.website_account_dao import WebsiteAccountDao
from module_admin.entity.vo.website_account_vo import (
    WebsiteAccountPageQueryModel, AddWebsiteAccountModel,
    EditWebsiteAccountModel, DeleteWebsiteAccountModel,
    SetWebsiteAccountStatusModel, WebsiteAccountImportResponseModel,
    WebsiteAccountImportTempModel
)
from exceptions.exception import ServiceException

logger = logging.getLogger(__name__)

class WebsiteAccountService:
    """网站账号管理服务层"""

    @classmethod
    async def get_website_account_list_services(
            cls, query_db: AsyncSession, query_object: WebsiteAccountPageQueryModel, is_page: bool = False
    ) -> PageModel | List[dict]:
        """获取网站账号列表"""
        try:
            return await WebsiteAccountDao.get_website_account_list(query_db, query_object, is_page)
        except Exception as e:
            raise ServiceException(message=f'获取网站账号列表失败：{str(e)}') from e

    @classmethod
    async def website_account_detail_services(cls, query_db: AsyncSession, account_id: int) -> dict:
        """获取网站账号详情"""
        account_info = await WebsiteAccountDao.get_website_account_detail_by_id(query_db, account_id)
        if not account_info:
            raise ServiceException(message=f'网站账号信息不存在，ID：{account_id}')
        return account_info

    @classmethod
    async def add_website_account_services(
            cls, query_db: AsyncSession, account: AddWebsiteAccountModel
    ) -> CrudResponseModel:
        """新增网站账号"""
        try:
            await WebsiteAccountDao.add_website_account_dao(query_db, account)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'新增失败：{str(e)}') from e

    @classmethod
    async def edit_website_account_services(
            cls, query_db: AsyncSession, account: EditWebsiteAccountModel
    ) -> CrudResponseModel:
        """编辑网站账号"""
        account_info = await WebsiteAccountDao.get_website_account_detail_by_id(query_db, account.id)
        if not account_info:
            raise ServiceException(message=f'网站账号信息不存在，ID：{account.id}')

        try:
            await WebsiteAccountDao.edit_website_account_dao(query_db, account)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            logger.error(f'编辑网站账号失败：{str(e)}', exc_info=True)
            raise ServiceException(message=f'修改失败：{str(e)}') from e

    @classmethod
    async def delete_website_account_services(
            cls, query_db: AsyncSession, page_object: DeleteWebsiteAccountModel
    ) -> CrudResponseModel:
        """删除网站账号（软删除）"""
        if not page_object.ids:
            raise ServiceException(message='传入网站账号 id 为空')

        try:
            account_ids = [int(id_str.strip()) for id_str in page_object.ids.split(',') if id_str.strip()]
            if not account_ids:
                raise ServiceException(message='网站账号 ID 格式错误，应为数字，多个用逗号分隔')

            delete_time = int(datetime.now().timestamp())
            await WebsiteAccountDao.delete_website_account_dao(query_db, account_ids, delete_time)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except ValueError:
            raise ServiceException(message='网站账号 ID 必须为数字，多个用逗号分隔')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'删除失败：{str(e)}') from e

    @classmethod
    async def set_website_account_status_services(
            cls, query_db: AsyncSession, page_object: SetWebsiteAccountStatusModel
    ) -> CrudResponseModel:
        """设置网站账号状态"""
        account_info = await WebsiteAccountDao.get_website_account_detail_by_id(query_db, page_object.id)
        if not account_info:
            raise ServiceException(message=f'网站账号信息不存在，ID：{page_object.id}')

        try:
            await WebsiteAccountDao.set_website_account_status_dao(query_db, page_object.id, page_object.status)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='设置成功')
        except Exception as e:
            await query_db.rollback()
            raise ServiceException(message=f'设置失败：{str(e)}') from e

    @classmethod
    async def generate_website_account_import_template(cls) -> BytesIO:
        """生成网站账号导入 Excel 模板"""
        try:
            field_mapping = {
                'website_name': '网站名称 (必填)',
                'website_url': '网址 (必填)',
                'username': '用户名',
                'password': '密码',
                'has_uk': '是否有 UK',
                'sort': '排序 (数字)',
                'remark': '说明'
            }

            headers = list(field_mapping.keys())
            header_notes = list(field_mapping.values())

            sample_data = [
                {
                    'website_name': '勾股 OA 官网',
                    'website_url': 'https://www.gouguoa.com',
                    'username': 'admin',
                    'password': '123456',
                    'has_uk': '否',
                    'sort': '1',
                    'remark': '示例账号'
                }
            ]

            df_notes = pd.DataFrame([header_notes], columns=headers)
            df_data = pd.DataFrame(sample_data, columns=headers)
            df = pd.concat([df_notes, df_data], ignore_index=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='网站账号模板', index=False, header=True)
                worksheet = writer.sheets['网站账号模板']

                for cell in worksheet[1]:
                    cell.font = Font(bold=True)
                for cell in worksheet[2]:
                    cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")

                for col in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in col)
                    worksheet.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

            output.seek(0)
            return output
        except Exception as e:
            logger.error(f"生成模板失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'生成模板失败：{str(e)}') from e

    @classmethod
    async def import_website_account_services(
            cls, query_db: AsyncSession, file: UploadFile
    ) -> WebsiteAccountImportResponseModel:
        """批量导入网站账号信息"""
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise ServiceException(message='仅支持 Excel 文件（.xlsx/.xls）导入')

        try:
            contents = await file.read()
            df = pd.read_excel(
                BytesIO(contents),
                sheet_name=0,
                header=0,
                skiprows=[1],
                dtype=str
            )

            df.columns = df.columns.str.strip()
            df = df.dropna(how='all').fillna('').reset_index(drop=True)

            model_fields = WebsiteAccountImportTempModel.model_fields.keys()
            for field in model_fields:
                if field not in df.columns:
                    df[field] = ''
            df = df[model_fields]
            excel_data = df.to_dict('records')

            success_count = 0
            fail_count = 0
            fail_data = []

            for idx, row in enumerate(excel_data):
                row_num = idx + 3
                try:
                    required_fields = ['website_name', 'website_url']
                    missing_fields = [f for f in required_fields if not str(row.get(f, '')).strip()]
                    if missing_fields:
                        raise ServiceException(f'必填字段为空：{",".join(missing_fields)}')

                    import_model = WebsiteAccountImportTempModel(**row)

                    add_model = AddWebsiteAccountModel(
                        website_name=import_model.website_name.strip(),
                        website_url=import_model.website_url.strip(),
                        username=import_model.username.strip() or None,
                        password=import_model.password.strip() or None,
                        has_uk=import_model.has_uk.strip() or None,
                        remark=import_model.remark.strip() or None,
                        sort=int(import_model.sort.strip()) if import_model.sort.strip() else 0
                    )

                    await WebsiteAccountDao.add_website_account_dao(query_db, add_model)
                    success_count += 1

                except Exception as e:
                    fail_count += 1
                    fail_data.append({
                        'row': row_num,
                        'data': row,
                        'reason': str(e)
                    })
                    logger.error(f"第{row_num}行导入失败：{str(e)}")
                    continue

            await query_db.commit()
            logger.info(f"导入完成：成功{success_count}条，失败{fail_count}条")

            return WebsiteAccountImportResponseModel(
                is_success=True,
                message=f'导入完成：成功{success_count}条，失败{fail_count}条',
                success_count=success_count,
                fail_count=fail_count,
                fail_data=fail_data
            )

        except Exception as e:
            await query_db.rollback()
            logger.error(f"导入网站账号信息失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'导入失败：{str(e)}') from e
