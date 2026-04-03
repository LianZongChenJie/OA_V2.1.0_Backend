from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.product_cate_dao import ProductCateDao
from module_admin.entity.vo.product_cate_vo import (
    AddProductCateModel,
    DeleteProductCateModel,
    EditProductCateModel,
    ProductCateModel,
    ProductCatePageQueryModel,
    ProductCateTreeModel,
)
from utils.common_util import CamelCaseUtil


class ProductCateService:
    """
    产品分类管理服务层
    """

    @classmethod
    async def get_product_cate_list_services(
            cls, query_db: AsyncSession, query_object: ProductCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取产品分类列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品分类列表信息对象
        """
        product_cate_list_result = await ProductCateDao.get_product_cate_list(query_db, query_object, is_page)

        return product_cate_list_result

    @classmethod
    async def get_product_cate_tree_services(cls, query_db: AsyncSession, pid: int | None = None) -> list[dict[str, Any]]:
        """
        获取产品分类树信息 service

        :param query_db: orm 对象
        :param pid: 父分类 ID，如果为 None 则返回完整树，否则返回指定 pid 下的子分类（扁平列表）
        :return: 产品分类树信息对象
        """
        if pid is not None:
            # 如果指定了 pid，只返回该 pid 下的直接子分类（不构成树形结构）
            product_cate_list_result = await ProductCateDao.get_product_cate_children_list(query_db, pid)
            # 转换为树模型格式（扁平列表）
            _product_cate_list = []
            for item in product_cate_list_result:
                cate_dict = item.copy()
                cate_dict['label'] = item.get('title')
                cate_dict['parentId'] = item.get('pid')
                _product_cate_list.append(ProductCateTreeModel(**cate_dict))
            return CamelCaseUtil.transform_result(_product_cate_list)
        else:
            # 如果没有指定 pid，返回完整的树形结构
            product_cate_list_result = await ProductCateDao.get_all_product_cate_list(query_db)
            product_cate_tree_result = cls.list_to_tree(product_cate_list_result)
            return CamelCaseUtil.transform_result(product_cate_tree_result)

    @classmethod
    def list_to_tree(cls, product_cate_list: list[dict[str, Any]]) -> list[ProductCateTreeModel]:
        """
        工具方法：根据分类列表信息生成树形嵌套数据

        :param product_cate_list: 分类列表信息
        :return: 分类树形嵌套数据
        """
        # 先创建基础模型列表，添加 label 和 parentId 字段用于构建树
        _product_cate_list = []
        for item in product_cate_list:
            cate_dict = item.copy()
            # 将 pid 转换为 parentId（驼峰命名）
            cate_dict['label'] = item.get('title')
            cate_dict['parentId'] = item.get('pid')
            _product_cate_list.append(ProductCateTreeModel(**cate_dict))
        
        # 转成 id 为 key 的字典
        mapping: dict[int, ProductCateTreeModel] = dict(
            zip([i.id for i in _product_cate_list], _product_cate_list, strict=False)
        )

        # 树容器
        container: list[ProductCateTreeModel] = []

        for d in _product_cate_list:
            # 如果找不到父级项，则是根节点
            parent = mapping.get(d.parentId)
            if parent is None or d.parentId == 0:
                container.append(d)
            else:
                children: list[ProductCateTreeModel] = parent.children
                if not children:
                    children = []
                children.append(d)
                parent.children = children

        return container

    @classmethod
    async def check_product_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: ProductCateModel
    ) -> bool:
        """
        校验产品分类名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 产品分类对象
        :return: 校验结果
        """
        product_cate_id = -1 if page_object.id is None else page_object.id
        product_cate = await ProductCateDao.get_product_cate_detail_by_info(query_db, page_object)
        if product_cate and product_cate.id != product_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def check_product_cate_parent_allowed(cls, query_db: AsyncSession, id: int, pid: int) -> bool:
        """
        检查父级分类是否允许设置（不能是本身或其子分类）

        :param query_db: orm 对象
        :param id: 当前分类 ID
        :param pid: 父分类 ID
        :return: 是否允许设置
        """
        if pid == 0:
            return True

        # 获取所有子分类 ID
        child_ids = await cls.get_child_product_cate_ids(query_db, id)
        if pid in child_ids or pid == id:
            return False
        return True

    @classmethod
    async def get_child_product_cate_ids(cls, query_db: AsyncSession, cate_id: int) -> list[int]:
        """
        递归获取所有子分类 ID

        :param query_db: orm 对象
        :param cate_id: 分类 ID
        :return: 子分类 ID 列表
        """
        child_ids = [cate_id]

        # 查询直接子分类
        all_categories = await ProductCateDao.get_all_product_cate_list(query_db)
        direct_children = [item for item in all_categories if item.get('pid') == cate_id]

        for child in direct_children:
            child_id = child.get('id')
            if child_id and child_id not in child_ids:
                child_ids.append(child_id)
                # 递归获取子分类的子分类
                grandchild_ids = await cls.get_child_product_cate_ids(query_db, child_id)
                child_ids.extend(grandchild_ids)

        return child_ids

    @classmethod
    async def add_product_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddProductCateModel, current_user_id: int = 0
    ) -> CrudResponseModel:
        """
        新增产品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增产品对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增产品校验结果
        """
        if not await cls.check_product_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增分类{page_object.title}失败，分类名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_product_cate = ProductCateModel(
                title=page_object.title,
                pid=page_object.pid if page_object.pid is not None else 0,
                sort=page_object.sort if page_object.sort is not None else 0,
                desc=page_object.desc,
                status=page_object.status if page_object.status is not None else 1,
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time
            )
            await ProductCateDao.add_product_cate_dao(query_db, add_product_cate)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_product_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProductCateModel
    ) -> CrudResponseModel:
        """
        编辑产品信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑产品对象
        :return: 编辑产品校验结果
        """
        edit_product_cate = page_object.model_dump(exclude_unset=True)
        product_cate_info = await cls.product_cate_detail_services(query_db, page_object.id)

        if product_cate_info.id:
            if not await cls.check_product_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改分类{page_object.title}失败，分类名称已存在')

            # 检查父级分类是否合法
            if not await cls.check_product_cate_parent_allowed(query_db, page_object.id, page_object.pid or 0):
                raise ServiceException(message='父级分类不能是该分类本身或其子分类')

            try:
                edit_product_cate['update_time'] = int(datetime.now().timestamp())
                await ProductCateDao.edit_product_cate_dao(query_db, edit_product_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='分类不存在')

    @classmethod
    async def delete_product_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeleteProductCateModel
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
                # 检查是否有子分类
                child_count = await ProductCateDao.count_child_product_cate_dao(query_db, page_object.id)
                if child_count > 0:
                    raise ServiceException(message='该分类下还有子分类，无法删除')

                product_cate = await cls.product_cate_detail_services(query_db, page_object.id)
                if not product_cate.id:
                    raise ServiceException(message='分类不存在')

                update_time = int(datetime.now().timestamp())
                await ProductCateDao.delete_product_cate_dao(
                    query_db,
                    ProductCateModel(id=page_object.id, update_time=update_time)
                )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入分类 id 为空')

    @classmethod
    async def set_product_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditProductCateModel
    ) -> CrudResponseModel:
        """
        设置产品分类状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置产品分类状态对象
        :return: 设置产品分类状态校验结果
        """
        product_cate_info = await cls.product_cate_detail_services(query_db, page_object.id)

        if product_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await ProductCateDao.disable_product_cate_dao(
                        query_db,
                        ProductCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await ProductCateDao.enable_product_cate_dao(
                        query_db,
                        ProductCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='分类不存在')

    @classmethod
    async def product_cate_detail_services(cls, query_db: AsyncSession, product_cate_id: int) -> ProductCateModel:
        """
        获取产品分类详细信息 service

        :param query_db: orm 对象
        :param product_cate_id: 分类 ID
        :return: 分类 ID 对应的信息
        """
        product_cate = await ProductCateDao.get_product_cate_detail_by_id(query_db, product_cate_id)
        result = ProductCateModel(**CamelCaseUtil.transform_result(product_cate)) if product_cate else ProductCateModel()

        return result

