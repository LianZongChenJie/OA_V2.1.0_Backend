from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.product_dao import ProductDao
from module_admin.entity.vo.product_vo import (
    AddProductModel,
    DeleteProductModel,
    EditProductModel,
    ProductModel,
    ProductPageQueryModel,
)
from utils.common_util import CamelCaseUtil


class ProductService:
    """
    产品管理服务层
    """

    @classmethod
    async def get_product_list_services(
            cls, query_db: AsyncSession, query_object: ProductPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取产品列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品列表信息对象
        """
        product_list_result = await ProductDao.get_product_list(query_db, query_object, is_page)

        return product_list_result

    @classmethod
    async def check_product_title_unique_services(
            cls, query_db: AsyncSession, page_object: ProductModel
    ) -> bool:
        """
        校验产品名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 产品对象
        :return: 校验结果
        """
        product_id = -1 if page_object.id is None else page_object.id
        product = await ProductDao.get_product_detail_by_info(query_db, page_object)
        if product and product.id != product_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_product_code_unique_services(
            cls, query_db: AsyncSession, page_object: ProductModel
    ) -> bool:
        """
        校验产品编码是否唯一 service

        :param query_db: orm 对象
        :param page_object: 产品对象
        :return: 校验结果
        """
        product_id = -1 if page_object.id is None else page_object.id
        if page_object.code:
            product = await ProductDao.get_product_detail_by_info(query_db, page_object)
            if product and product.id != product_id:
                return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_product_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddProductModel, current_user_id: int = 0
    ) -> CrudResponseModel:
        """
        新增产品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增产品对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增产品校验结果
        """
        if not await cls.check_product_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增产品{page_object.title}失败，产品名称已存在')

        if not await cls.check_product_code_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增产品{page_object.title}失败，产品编码已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_product = ProductModel(
                title=page_object.title,
                cate_id=page_object.cate_id if page_object.cate_id is not None else 0,
                thumb=page_object.thumb if page_object.thumb is not None else 0,
                code=page_object.code,
                barcode=page_object.barcode,
                unit=page_object.unit,
                specs=page_object.specs,
                brand=page_object.brand,
                producer=page_object.producer,
                base_price=page_object.base_price if page_object.base_price is not None else 0,
                purchase_price=page_object.purchase_price if page_object.purchase_price is not None else 0,
                sale_price=page_object.sale_price if page_object.sale_price is not None else 0,
                content=page_object.content,
                album_ids=page_object.album_ids if page_object.album_ids else '',
                file_ids=page_object.file_ids if page_object.file_ids else '',
                stock=page_object.stock if page_object.stock is not None else 0,
                is_object=page_object.is_object if page_object.is_object is not None else 1,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time,

            )
            await ProductDao.add_product_dao(query_db, add_product)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_product_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProductModel
    ) -> CrudResponseModel:
        """
        编辑产品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑产品对象
        :return: 编辑产品校验结果
        """
        edit_product = page_object.model_dump(exclude_unset=True)
        product_info = await cls.product_detail_services(query_db, page_object.id)

        if product_info.id:
            if not await cls.check_product_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改产品{page_object.title}失败，产品名称已存在')

            if not await cls.check_product_code_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改产品{page_object.title}失败，产品编码已存在')

            try:
                edit_product['update_time'] = int(datetime.now().timestamp())
                await ProductDao.edit_product_dao(query_db, edit_product)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='产品不存在')

    @classmethod
    async def delete_product_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteProductModel
    ) -> CrudResponseModel:
        """
        删除产品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除产品对象
        :return: 删除产品校验结果
        """
        if page_object.id:
            try:
                product = await cls.product_detail_services(query_db, page_object.id)
                if not product.id:
                    raise ServiceException(message='产品不存在')

                update_time = int(datetime.now().timestamp())
                await ProductDao.delete_product_dao(
                    query_db,
                    ProductModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入产品 id 为空')

    @classmethod
    async def set_product_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProductModel
    ) -> CrudResponseModel:
        """
        设置产品状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置产品状态对象
        :return: 设置产品状态校验结果
        """
        product_info = await cls.product_detail_services(query_db, page_object.id)

        if product_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await ProductDao.disable_product_dao(
                        query_db,
                        ProductModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await ProductDao.enable_product_dao(
                        query_db,
                        ProductModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='产品不存在')

    @classmethod
    async def product_detail_services(cls, query_db: AsyncSession, product_id: int) -> ProductModel:
        """
        获取产品详细信息 service

        :param query_db: orm 对象
        :param product_id: 产品 id
        :return: 产品 id 对应的信息
        """
        product = await ProductDao.get_product_detail_by_id(query_db, product_id)
        result = ProductModel(**CamelCaseUtil.transform_result(product)) if product else ProductModel()

        return result

