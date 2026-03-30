import io
from datetime import datetime
from typing import Any
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl.styles import PatternFill, Font
from io import BytesIO

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_admin.entity.vo.import_vo import AdminImportTempModel, ImportResponseModel
from utils.log_util import logger


class AdminImportService:
    """员工导入服务层"""

    @classmethod
    async def generate_admin_import_template(cls) -> BytesIO:
        """生成员工导入 Excel 模板"""
        try:
            field_mapping = {
                'name': '姓名 (必填)',
                'mobile': '手机号码 (必填)',
                'email': '电子邮箱',
                'sex': '性别 (男/女/未知)',
                'department': '所在部门',
                'position': '所属职位',
                'type': '员工类型 (正式/试用/实习)',
                'entry_time': '入职日期 (格式：YYYY-MM-DD)'
            }

            headers = list(field_mapping.keys())
            header_notes = list(field_mapping.values())

            sample_data = [
                {
                    'name': '张三',
                    'mobile': '13800138000',
                    'email': 'zhangsan@example.com',
                    'sex': '男',
                    'department': '技术部',
                    'position': '工程师',
                    'type': '正式',
                    'entry_time': '2024-01-01'
                }
            ]

            df_notes = pd.DataFrame([header_notes], columns=headers)
            df_data = pd.DataFrame(sample_data, columns=headers)
            df = pd.concat([df_notes, df_data], ignore_index=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='员工模板', index=False, header=True)
                worksheet = writer.sheets['员工模板']

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
            logger.error(f"生成员工模板失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'生成员工模板失败：{str(e)}') from e

    @classmethod
    async def import_admin_services(
            cls,
            query_db: AsyncSession,
            file: UploadFile,
            current_user_id: int
    ) -> ImportResponseModel:
        """批量导入员工"""
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

            model_fields = AdminImportTempModel.model_fields.keys()
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
                    required_fields = ['name', 'mobile']
                    missing_fields = [f for f in required_fields if not str(row.get(f, '')).strip()]
                    if missing_fields:
                        raise ServiceException(f'必填字段为空：{",".join(missing_fields)}')

                    import_model = AdminImportTempModel(**row)

                    if not import_model.name.strip():
                        raise ServiceException('姓名不能为空')

                    if not import_model.mobile.strip():
                        raise ServiceException('手机号码不能为空')

                    add_admin = {
                        'name': import_model.name.strip(),
                        'nickname': import_model.name.strip(),
                        'mobile': import_model.mobile.strip(),
                        'email': import_model.email.strip() if import_model.email else '',
                        'sex': cls._convert_sex(import_model.sex),
                        'type': cls._convert_employee_type(import_model.type),
                        'entry_time': cls._parse_date(import_model.entry_time),
                        'admin_id': current_user_id,
                        'create_time': int(datetime.now().timestamp()),
                        'update_time': int(datetime.now().timestamp()),
                        'delete_time': 0
                    }

                    await query_db.execute(
                        "INSERT INTO sys_user (name, nickname, mobile, email, sex, type, entry_time, admin_id, create_time, update_time, delete_time) VALUES (:name, :nickname, :mobile, :email, :sex, :type, :entry_time, :admin_id, :create_time, :update_time, :delete_time)",
                        add_admin
                    )
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

            return ImportResponseModel(
                is_success=True,
                message=f'导入完成：成功{success_count}条，失败{fail_count}条',
                success_count=success_count,
                fail_count=fail_count,
                fail_data=fail_data
            )

        except Exception as e:
            await query_db.rollback()
            logger.error(f"导入员工失败：{str(e)}", exc_info=True)
            raise ServiceException(message=f'导入失败：{str(e)}') from e

    @staticmethod
    def _convert_sex(sex_str: str) -> int:
        """转换性别：未知->0, 男->1, 女->2"""
        sex_map = {
            '未知': 0,
            '男': 1,
            '女': 2
        }
        return sex_map.get(sex_str.strip(), 0)

    @staticmethod
    def _convert_employee_type(type_str: str) -> int:
        """转换员工类型：未知->0, 正式->1, 试用->2, 实习->3"""
        type_map = {
            '未知': 0,
            '正式': 1,
            '试用': 2,
            '实习': 3
        }
        return type_map.get(type_str.strip(), 0)

    @staticmethod
    def _parse_date(date_str: str) -> int | None:
        """解析日期字符串为时间戳"""
        if not date_str or not date_str.strip():
            return None
        try:
            dt = datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return int(dt.timestamp())
        except ValueError:
            return None
