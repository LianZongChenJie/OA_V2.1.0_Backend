from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.supplier_dao import SupplierDao
from module_admin.entity.vo.supplier_vo import (
    AddSupplierModel,
    DeleteSupplierModel,
    EditSupplierModel,
    SupplierModel,
    SupplierPageQueryModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class SupplierService:
    """
    供应商管理模块服务层
    """

    @classmethod
    async def get_supplier_list_services(
            cls, query_db: AsyncSession, query_object: SupplierPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取供应商列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 供应商列表信息对象
        """
        supplier_list_result = await SupplierDao.get_supplier_list(query_db, query_object, is_page)

        return supplier_list_result

    @classmethod
    async def check_supplier_title_unique_services(
            cls, query_db: AsyncSession, page_object: SupplierModel
    ) -> bool:
        """
        校验供应商名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 供应商对象
        :return: 校验结果
        """
        supplier_id = -1 if page_object.id is None else page_object.id
        supplier = await SupplierDao.get_supplier_detail_by_info(query_db, page_object)
        if supplier and supplier.id != supplier_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_supplier_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddSupplierModel
    ) -> CrudResponseModel:
        """
        新增供应商信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增供应商对象
        :return: 新增供应商校验结果
        """
        if not await cls.check_supplier_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增供应商{page_object.title}失败，供应商名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_supplier = SupplierModel(
                title=page_object.title,
                code=page_object.code if page_object.code is not None else '',
                phone=page_object.phone if page_object.phone is not None else '',
                email=page_object.email if page_object.email is not None else '',
                address=page_object.address if page_object.address is not None else '',
                file_ids=page_object.file_ids if page_object.file_ids is not None else '',
                products=page_object.products if page_object.products is not None else '',
                content=page_object.content,
                status=page_object.status if page_object.status is not None else 1,
                tax_num=page_object.tax_num if page_object.tax_num is not None else '',
                tax_mobile=page_object.tax_mobile if page_object.tax_mobile is not None else '',
                tax_address=page_object.tax_address if page_object.tax_address is not None else '',
                tax_bank=page_object.tax_bank if page_object.tax_bank is not None else '',
                tax_banksn=page_object.tax_banksn if page_object.tax_banksn is not None else '',
                file_license_ids=page_object.file_license_ids if page_object.file_license_ids is not None else '',
                file_idcard_ids=page_object.file_idcard_ids if page_object.file_idcard_ids is not None else '',
                file_bankcard_ids=page_object.file_bankcard_ids if page_object.file_bankcard_ids is not None else '',
                file_openbank_ids=page_object.file_openbank_ids if page_object.file_openbank_ids is not None else '',
                tax_rate=page_object.tax_rate if page_object.tax_rate is not None else 0.00,
                admin_id=page_object.admin_id if page_object.admin_id is not None else 0,
                sort=page_object.sort if page_object.sort is not None else 0,
                create_time=current_time,
                update_time=current_time,
                delete_time=0
            )
            logger.info(f'Service 层准备插入的数据：title={add_supplier.title}, create_time={add_supplier.create_time}')
            await SupplierDao.add_supplier_dao(query_db, add_supplier)
            await query_db.commit()
            logger.info(f'新增成功，生成的 ID: {add_supplier.id}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_supplier_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSupplierModel
    ) -> CrudResponseModel:
        """
        编辑供应商信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑供应商对象
        :return: 编辑供应商校验结果
        """
        edit_supplier = page_object.model_dump(exclude_unset=True)
        supplier_info = await cls.supplier_detail_services(query_db, page_object.id)

        if supplier_info.id:
            if not await cls.check_supplier_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改供应商{page_object.title}失败，供应商名称已存在')

            try:
                edit_supplier['update_time'] = int(datetime.now().timestamp())
                await SupplierDao.edit_supplier_dao(query_db, edit_supplier)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='供应商不存在')

    @classmethod
    async def delete_supplier_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteSupplierModel
    ) -> CrudResponseModel:
        """
        删除供应商信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除供应商对象
        :return: 删除供应商校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for supplier_id in id_list:
                    supplier = await cls.supplier_detail_services(query_db, int(supplier_id))
                    if not supplier.id:
                        raise ServiceException(message='供应商不存在')

                    update_time = int(datetime.now().timestamp())
                    await SupplierDao.delete_supplier_dao(
                        query_db,
                        SupplierModel(id=int(supplier_id), update_time=update_time),
                        page_object.type
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入供应商 id 为空')

    @classmethod
    async def set_supplier_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditSupplierModel
    ) -> CrudResponseModel:
        """
        设置供应商状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置供应商对象
        :return: 设置供应商状态校验结果
        """
        supplier_info = await cls.supplier_detail_services(query_db, page_object.id)

        if supplier_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await SupplierDao.disable_supplier_dao(
                        query_db,
                        SupplierModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await SupplierDao.enable_supplier_dao(
                        query_db,
                        SupplierModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='供应商不存在')

    @classmethod
    async def supplier_detail_services(cls, query_db: AsyncSession, supplier_id: int) -> SupplierModel:
        """
        获取供应商详细信息 service

        :param query_db: orm 对象
        :param supplier_id: 供应商 id
        :return: 供应商 id 对应的信息
        """
        supplier = await SupplierDao.get_supplier_detail_by_id(query_db, supplier_id)
        result = SupplierModel(**CamelCaseUtil.transform_result(supplier)) if supplier else SupplierModel()

        return result
