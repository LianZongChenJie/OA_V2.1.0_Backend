from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.purchased_cate_dao import PurchasedCateDao
from module_admin.entity.vo.purchased_cate_vo import (
    AddPurchasedCateModel,
    DeletePurchasedCateModel,
    EditPurchasedCateModel,
    PurchasedCateModel,
    PurchasedCatePageQueryModel,
    PurchasedCateTreeModel,
)
from utils.common_util import CamelCaseUtil
from utils.log_util import logger


class PurchasedCateService:
    """
    采购品分类管理服务层
    """

    @classmethod
    async def get_purchased_cate_list_services(
            cls, query_db: AsyncSession, query_object: PurchasedCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取采购品分类列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 采购品分类列表信息对象
        """
        purchased_cate_list_result = await PurchasedCateDao.get_purchased_cate_list(query_db, query_object, is_page)

        return purchased_cate_list_result

    @classmethod
    async def get_purchased_cate_tree_services(cls, query_db: AsyncSession) -> list[PurchasedCateTreeModel]:
        """
        获取采购品分类树形结构 service

        :param query_db: orm 对象
        :return: 分类树形结构对象
        """
        all_categories = await PurchasedCateDao.get_all_purchased_cate_list(query_db)

        # 转换为字典列表
        _purchased_cate_list = []
        for cate in all_categories:
            cate_dict = cate.to_dict()
            cate_dict['label'] = cate.title
            _purchased_cate_list.append(PurchasedCateTreeModel(**cate_dict))

        # 转成 id 为 key 的字典
        mapping: dict[int, PurchasedCateTreeModel] = dict(
            zip([i.id for i in _purchased_cate_list], _purchased_cate_list, strict=False)
        )

        # 树容器
        container: list[PurchasedCateTreeModel] = []

        for d in _purchased_cate_list:
            # 如果找不到父级项，则是根节点
            parent = mapping.get(d.pid)
            if parent is None or d.pid == 0:
                container.append(d)
            else:
                children: list[PurchasedCateTreeModel] = parent.children
                if not children:
                    children = []
                children.append(d)
                parent.children = children

        return container

    @classmethod
    async def check_purchased_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: PurchasedCateModel
    ) -> bool:
        """
        校验采购品分类名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 采购品分类对象
        :return: 校验结果
        """
        purchased_cate_id = -1 if page_object.id is None else page_object.id
        purchased_cate = await PurchasedCateDao.get_purchased_cate_detail_by_info(query_db, page_object)
        if purchased_cate and purchased_cate.id != purchased_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def get_child_purchased_cate_ids(cls, query_db: AsyncSession, cate_id: int) -> list[int]:
        """
        获取分类的所有子分类 ID（递归）

        :param query_db: orm 对象
        :param cate_id: 分类 ID
        :return: 子分类 ID 列表
        """
        child_ids = []

        # 获取所有分类
        all_categories = await PurchasedCateDao.get_all_purchased_cate_list(query_db)
        all_categories_dict = [cate.to_dict() for cate in all_categories]

        # 递归获取直接子分类
        direct_children = [item for item in all_categories_dict if item.get('pid') == cate_id]

        for child in direct_children:
            child_id = child.get('id')
            if child_id and child_id not in child_ids:
                child_ids.append(child_id)
                # 递归获取子分类的子分类
                grandchild_ids = await cls.get_child_purchased_cate_ids(query_db, child_id)
                child_ids.extend(grandchild_ids)

        return child_ids

    @classmethod
    async def add_purchased_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: AddPurchasedCateModel, current_user_id: int = 0
    ) -> CrudResponseModel:
        """
        新增采购品分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增采购品分类对象
        :param current_user_id: 当前登录用户 ID
        :return: 新增采购品分类校验结果
        """
        if not await cls.check_purchased_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增分类{page_object.title}失败，分类名称已存在')

        try:
            current_time = int(datetime.now().timestamp())
            add_purchased_cate = PurchasedCateModel(
                title=page_object.title,
                pid=page_object.pid if page_object.pid is not None else 0,
                sort=page_object.sort if page_object.sort is not None else 0,
                desc=page_object.desc if page_object.desc is not None else '',
                status=page_object.status if page_object.status is not None else 1,
                admin_id=current_user_id,
                create_time=current_time,
                update_time=current_time
            )
            logger.info(f'Service 层准备插入的数据：title={add_purchased_cate.title}, pid={add_purchased_cate.pid}')
            await PurchasedCateDao.add_purchased_cate_dao(query_db, add_purchased_cate)
            await query_db.commit()
            logger.info(f'新增成功，生成的 ID: {add_purchased_cate.id}')
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_purchased_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPurchasedCateModel
    ) -> CrudResponseModel:
        """
        编辑采购品分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑采购品分类对象
        :return: 编辑采购品分类校验结果
        """
        edit_purchased_cate = page_object.model_dump(exclude_unset=True)
        purchased_cate_info = await cls.purchased_cate_detail_services(query_db, page_object.id)

        if purchased_cate_info.id:
            # 检查父级分类是否合法（不能是自身或子分类）
            if page_object.pid is not None and page_object.pid > 0:
                child_ids = await cls.get_child_purchased_cate_ids(query_db, page_object.id)
                if page_object.pid in child_ids:
                    raise ServiceException(message='父级分类不能是该分类本身或其子分类')

            if not await cls.check_purchased_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改分类{page_object.title}失败，分类名称已存在')

            try:
                edit_purchased_cate['update_time'] = int(datetime.now().timestamp())
                await PurchasedCateDao.edit_purchased_cate_dao(query_db, edit_purchased_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='分类不存在')

    @classmethod
    async def delete_purchased_cate_services(
            cls, request: Request, query_db: AsyncSession, page_object: DeletePurchasedCateModel
    ) -> CrudResponseModel:
        """
        删除采购品分类信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除采购品分类对象
        :return: 删除采购品分类校验结果
        """
        try:
            # 检查是否有子分类
            has_children = await PurchasedCateDao.has_children(query_db, page_object.id)
            if has_children:
                raise ServiceException(message='该分类下还有子分类，无法删除')

            # 检查是否有产品关联（需要在 Product 表中检查）
            # 这里需要根据实际情况添加检查逻辑

            await PurchasedCateDao.delete_purchased_cate_dao(query_db, page_object.id)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def set_purchased_cate_status_services(
            cls, request: Request, query_db: AsyncSession, page_object: EditPurchasedCateModel
    ) -> CrudResponseModel:
        """
        设置采购品分类状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置采购品分类状态对象
        :return: 设置采购品分类状态校验结果
        """
        purchased_cate_info = await cls.purchased_cate_detail_services(query_db, page_object.id)

        if purchased_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())

                if page_object.status == 0:
                    await PurchasedCateDao.disable_purchased_cate_dao(
                        query_db,
                        PurchasedCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await PurchasedCateDao.enable_purchased_cate_dao(
                        query_db,
                        PurchasedCateModel(id=page_object.id, update_time=update_time)
                    )

                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='分类不存在')

    @classmethod
    async def purchased_cate_detail_services(cls, query_db: AsyncSession, cate_id: int) -> PurchasedCateModel:
        """
        获取采购品分类详细信息 service

        :param query_db: orm 对象
        :param cate_id: 分类 id
        :return: 分类 id 对应的信息
        """
        cate = await PurchasedCateDao.get_purchased_cate_detail_by_id(query_db, cate_id)
        result = PurchasedCateModel(**CamelCaseUtil.transform_result(cate)) if cate else PurchasedCateModel()

        return result
