import io
from datetime import datetime
from typing import Any
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openpyxl.styles import PatternFill, Font
from io import BytesIO

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.import_vo import CustomerImportTempModel, ImportResponseModel
from module_admin.entity.do.customer_do import OaCustomer
from utils.log_util import logger


class CustomerImportService:
    """客户导入服务层"""

    @classmethod
    async def generate_customer_import_template(cls) -> BytesIO:
        """生成客户导入 Excel 模板"""
        try:
            field_mapping = {
                'name': '客户名称 (必填)',
                'source': '客户来源',
                'grade': '客户等级',
                'industry': '所属行业',
                'c_name': '联系人姓名 (必填)',
                'c_mobile': '联系人手机 (必填)',
                'tax_num': '纳税人识别号',
                'tax_bank': '开户银行',
                'tax_banksn': '银行帐号',
                'tax_mobile': '开票电话',
                'tax_address': '开票地址',
                'address': '联系地址',
                'content': '客户描述',
                'market': '主要经营业务'
            }

            headers = list(field_mapping.keys())
            header_notes = list(field_mapping.values())

            sample_data = [
                {
                    'name': '北京 XX 科技有限公司',
                    'source': '网络推广',
                    'grade': 'A 级',
                    'industry': '互联网',
                    'c_name': '李四',
                    'c_mobile': '13900139000',
                    'tax_num': '91110000XXXXXXXXXX',
                    'tax_bank': '中国工商银行',
                    'tax_banksn': '6222081100001234567',
                    'tax_mobile': '',
                    'tax_address': '',
                    'address': '北京市海淀区 XX 路 XX 号',
                    'content': '重点客户',
                    'market': '软件开发、技术服务'
                }
            ]

            df_notes = pd.DataFrame([header_notes], columns=headers)
            df_data = pd.DataFrame(sample_data, columns=headers)
            df = pd.concat([df_notes, df_data], ignore_index=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='客户模板', index=False, header=True)
                worksheet = writer.sheets['客户模板']

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
            logger.error(f"生成客户模板失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'生成客户模板失败：{str(e)}') from e

    @classmethod
    async def import_customer_services(
            cls,
            query_db: AsyncSession,
            file: UploadFile,
            current_user_id: int,
            belong_uid: int = 0,
            belong_did: int = 0,
            customer_type: str = 'sea'
    ) -> ImportResponseModel:
        """批量导入客户"""
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

            model_fields = CustomerImportTempModel.model_fields.keys()
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
                    required_fields = ['name', 'c_name', 'c_mobile']
                    missing_fields = [f for f in required_fields if not str(row.get(f, '')).strip()]
                    if missing_fields:
                        raise ServiceException(f'必填字段为空：{",".join(missing_fields)}')

                    import_model = CustomerImportTempModel(**row)

                    if not import_model.name.strip():
                        raise ServiceException('客户名称不能为空')

                    if not import_model.c_name.strip():
                        raise ServiceException('联系人姓名不能为空')

                    if not import_model.c_mobile.strip():
                        raise ServiceException('联系人手机不能为空')

                    belong_uid_val = belong_uid if customer_type != 'sea' else 0
                    belong_did_val = belong_did if customer_type != 'sea' else 0

                    # 校验客户名称是否唯一
                    logger.info(f"开始验重：客户名称={import_model.name.strip()}")
                    query = select(OaCustomer).where(
                        OaCustomer.name == import_model.name.strip(),
                        OaCustomer.delete_time == 0,
                        OaCustomer.discard_time == 0
                    )
                    result = await query_db.execute(query)
                    existing_customer = result.scalars().first()
                    logger.info(f"验重结果：existing_customer={existing_customer}")
                    
                    if existing_customer:
                        logger.warning(f"客户名称已存在：{import_model.name.strip()}")
                        raise ServiceException(f'客户名称"{import_model.name.strip()}"已存在')

                    add_customer = {
                        'name': import_model.name.strip(),
                        'source_id': 0,
                        'grade_id': 0,
                        'industry_id': 0,
                        'tax_num': import_model.tax_num.strip() if import_model.tax_num else '',
                        'tax_bank': import_model.tax_bank.strip() if import_model.tax_bank else '',
                        'tax_banksn': import_model.tax_banksn.strip() if import_model.tax_banksn else '',
                        'tax_mobile': import_model.tax_mobile.strip() if import_model.tax_mobile else '',
                        'tax_address': import_model.tax_address.strip() if import_model.tax_address else '',
                        'address': import_model.address.strip() if import_model.address else '',
                        'content': import_model.content.strip() if import_model.content else '',
                        'market': import_model.market.strip() if import_model.market else '',
                        'admin_id': current_user_id,
                        'belong_uid': belong_uid_val,
                        'belong_did': belong_did_val,
                        'create_time': int(datetime.now().timestamp()),
                        'update_time': int(datetime.now().timestamp()),
                        'delete_time': 0
                    }

                    db_customer = OaCustomer(**add_customer)
                    query_db.add(db_customer)
                    await query_db.flush()

                    customer_id = db_customer.id

                    if customer_id > 0:
                        success_count += 1
                    else:
                        raise ServiceException('客户 ID 生成失败')

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

            return ImportResponseModel(
                is_success=True,
                message=f'导入完成：成功{success_count}条，失败{fail_count}条',
                success_count=success_count,
                fail_count=fail_count,
                fail_data=fail_data if fail_data else None
            )

        except Exception as e:
            await query_db.rollback()
            logger.error(f"导入客户失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'导入失败：{str(e)}') from e
