from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.dao.contacts_book_dao import ContactsBookDao
from module_admin.entity.vo.user_vo import ContactsBookPageQueryModel
from utils.camel_converter import ModelConverter
from utils.common_util import CamelCaseUtil


class ContactsBookService:
    """
    通讯录服务层
    """

    @classmethod
    async def get_contacts_book_list_services(
        cls, query_db: AsyncSession, query_object: ContactsBookPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取通讯录列表信息服务

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 通讯录列表信息
        """
        contacts_result = await ContactsBookDao.get_contacts_book_list(query_db, query_object, is_page)

        # 如果返回的是分页结果，需要转换 rows 中的数据
        if hasattr(contacts_result, 'rows'):
            transformed_rows = []
            for row in contacts_result.rows:
                # row 是一个元组 (OaAdmin, department, position)
                if isinstance(row, (list, tuple)):
                    admin_obj = row[0]
                    extra_fields = {
                        'department': row[1] if len(row) > 1 else None,
                        'position': row[2] if len(row) > 2 else None,
                    }

                    # 将 ORM 对象转换为字典
                    admin_dict = CamelCaseUtil.transform_result(admin_obj)
                    # 合并扩展字段
                    admin_dict.update(extra_fields)
                    
                    # 格式化时间字段
                    admin_dict = ModelConverter.time_format(admin_dict)
                    
                    # 处理手机号隐藏
                    if admin_dict.get('isHide') == 1:
                        if admin_dict.get('mobile'):
                            phone = str(admin_dict['mobile'])
                            if len(phone) == 11:
                                admin_dict['mobile'] = phone[:3] + '****' + phone[7:]
                        if admin_dict.get('email'):
                            email = admin_dict['email']
                            if '@' in email:
                                parts = email.split('@')
                                admin_dict['email'] = parts[0][:2] + '***@' + parts[1]

                    # 获取次要部门
                    admin_dict['departments'] = '-'
                    
                    transformed_rows.append(admin_dict)
                else:
                    transformed_dict = CamelCaseUtil.transform_result(row)
                    transformed_dict = ModelConverter.time_format(transformed_dict)
                    transformed_rows.append(transformed_dict)

            contacts_result.rows = transformed_rows

        return contacts_result
