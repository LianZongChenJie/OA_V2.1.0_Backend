from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from common.vo import PageModel
from module_admin.entity.do.product_do import OaProduct
from module_admin.entity.do.product_cate_do import OaProductCate
from module_admin.entity.vo.product_vo import ProductModel, ProductPageQueryModel
from utils.page_util import PageUtil


class ProductDao:
    """
    产品管理模块数据库操作层
    """

    @classmethod
    async def get_product_detail_by_id(cls, db: AsyncSession, product_id: int) -> OaProduct | None:
        """
        根据产品 id 获取产品详细信息

        :param db: orm 对象
        :param product_id: 产品 id
        :return: 产品信息对象
        """
        product_info = (
            (await db.execute(select(OaProduct).where(OaProduct.id == product_id)))
            .scalars()
            .first()
        )

        return product_info

    @classmethod
    async def get_product_detail_by_info(cls, db: AsyncSession, product: ProductModel) -> OaProduct | None:
        """
        根据产品参数获取产品信息

        :param db: orm 对象
        :param product: 产品参数对象
        :return: 产品信息对象
        """
        query_conditions = []
        if product.title:
            query_conditions.append(OaProduct.title == product.title)
        if product.code:
            query_conditions.append(OaProduct.code == product.code)

        if query_conditions:
            product_info = (
                (await db.execute(select(OaProduct).where(and_(*query_conditions))))
                .scalars()
                .first()
            )
        else:
            product_info = None

        return product_info

    @classmethod
    async def get_product_list(
            cls, db: AsyncSession, query_object: ProductPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取产品列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品列表信息对象
        """
        # 定义产品分类表别名
        cate = aliased(OaProductCate)
        
        # 构建查询：关联产品分类表获取分类名称
        query = (
            select(
                OaProduct,
                cate.title.label('cate_name')  # 分类名称
            )
            .outerjoin(cate, and_(OaProduct.cate_id == cate.id, cate.status != -1))
            .where(
                OaProduct.status != -1,
                OaProduct.title.like(f'%{query_object.keywords}%') if query_object.keywords else True,
                OaProduct.cate_id == query_object.cate_id if query_object.cate_id is not None else True,
                OaProduct.status == query_object.status if query_object.status is not None else True,
                )
            .order_by(OaProduct.create_time.desc())
            .distinct()
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # 处理查询结果
        product_list = []
        for row in rows:
            product = row[0]
            cate_name = row[1] if row[1] else ''
            
            product_dict = {
                'id': product.id,
                'title': product.title,
                'cateId': product.cate_id,
                'cateName': cate_name,
                'thumb': product.thumb,
                'code': product.code,
                'barcode': product.barcode,
                'unit': product.unit,
                'specs': product.specs,
                'brand': product.brand,
                'producer': product.producer,
                'basePrice': float(product.base_price) if product.base_price else 0.0,
                'purchasePrice': float(product.purchase_price) if product.purchase_price else 0.0,
                'salePrice': float(product.sale_price) if product.sale_price else 0.0,
                'content': product.content,
                'albumIds': product.album_ids,
                'fileIds': product.file_ids,
                'stock': product.stock,
                'isObject': product.is_object,
                'status': product.status,
                'adminId': product.admin_id,
                'createTime': product.create_time,
                'updateTime': product.update_time,
                'deleteTime': product.delete_time,
            }
            product_list.append(product_dict)
        
        # 处理分页
        if is_page:
            total = len(product_list)
            start = (query_object.page_num - 1) * query_object.page_size
            end = start + query_object.page_size
            paginated_list = product_list[start:end]
            
            return PageModel(
                rows=paginated_list,
                pageNum=query_object.page_num,
                pageSize=query_object.page_size,
                total=total,
                hasNext=end < total
            )
        else:
            return product_list

    @classmethod
    async def add_product_dao(cls, db: AsyncSession, product: dict) -> OaProduct:
        """
        新增产品数据库操作

        :param db: orm 对象
        :param product: 产品字典
        :return:
        """
        db_product = OaProduct(**product)
        db.add(db_product)
        await db.flush()

        return db_product

    @classmethod
    async def edit_product_dao(cls, db: AsyncSession, product: dict) -> None:
        """
        编辑产品数据库操作

        :param db: orm 对象
        :param product: 需要更新的产品字典
        :return:
        """
        await db.execute(update(OaProduct), [product])

    @classmethod
    async def delete_product_dao(cls, db: AsyncSession, product: ProductModel) -> None:
        """
        删除产品数据库操作（逻辑删除）

        :param db: orm 对象
        :param product: 产品对象
        :return:
        """
        update_time = product.update_time if product.update_time is not None else int(datetime.now().timestamp())
        delete_time = update_time
        await db.execute(
            update(OaProduct)
            .where(OaProduct.id.in_([product.id]))
            .values(status=0, update_time=update_time, delete_time=delete_time)
        )

    @classmethod
    async def disable_product_dao(cls, db: AsyncSession, product: ProductModel) -> None:
        """
        禁用产品数据库操作

        :param db: orm 对象
        :param product: 产品对象
        :return:
        """
        update_time = product.update_time if product.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProduct)
            .where(OaProduct.id == product.id)
            .values(status=0, update_time=update_time)
        )

    @classmethod
    async def enable_product_dao(cls, db: AsyncSession, product: ProductModel) -> None:
        """
        启用产品数据库操作

        :param db: orm 对象
        :param product: 产品对象
        :return:
        """
        update_time = product.update_time if product.update_time is not None else int(datetime.now().timestamp())
        await db.execute(
            update(OaProduct)
            .where(OaProduct.id == product.id)
            .values(status=1, update_time=update_time)
        )