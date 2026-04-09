from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_basicdata.dao.public.area_dao import AreaDao
from module_basicdata.entity.do.public.arae_do import OaArea
from module_basicdata.entity.vo.public.area_vo import AreaTreeModel, AreaBaseModel


class AreaService:
    @classmethod
    async def get_list_tree(cls, db: AsyncSession, area: AreaBaseModel) -> list[AreaTreeModel]:
        return await AreaDao.get_area_tree(db, area)

    @classmethod
    async def save(cls, db: AsyncSession, area: AreaTreeModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(db, area):
            raise ServiceException(message=f'新增{area.name}失败，名称已存在')
        result = await AreaDao.add(db, area)
        if result:
            return CrudResponseModel(is_success=True, message="操作成功")
        else:
            return CrudResponseModel(is_success=False, message="操作失败")

    @classmethod
    async def delete(cls, db: AsyncSession, id: int) -> CrudResponseModel:
        result = await AreaDao.delete(db, id)
        if result:
            return CrudResponseModel(is_success=True, message="操作成功")
        else:
            return CrudResponseModel(is_success=False, message="操作失败")

    @classmethod
    async def change_status_area_service(cls, query_db: AsyncSession, model: AreaBaseModel) -> CrudResponseModel:
        try:
            await AreaDao.change_status_area(query_db, model)
            return CrudResponseModel(is_success=True, message='状态变更成功')
        except Exception as e:
            await query_db.rollback()
            raise e
        pass

    @classmethod
    async def get_area_by_id(cls, db: AsyncSession, area_id: int) -> AreaBaseModel:
        try:
            area_info = await AreaDao.get_by_id(db, area_id)
            if not area_info:
                raise ServiceException(message="未找到该数据")
            return area_info
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def update(cls, db: AsyncSession, model: AreaBaseModel) -> CrudResponseModel:
        if not await cls.check_name_unique_services(db, model):
            raise ServiceException(message=f'修改{model.name}失败，名称已存在')
        result = await AreaDao.update(db, model)
        if result:
            return CrudResponseModel(is_success=True, message="操作成功")
        else:
            return CrudResponseModel(is_success=False, message="操作失败")

    @classmethod
    async def get_area_by_level(cls, db: AsyncSession, level: int) -> AreaBaseModel:
        try:
            area_info = await AreaDao.get_area_by_level(db, level)
            if not area_info:
                raise ServiceException(message="未找到该数据")
            return area_info
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def check_name_unique_services(cls, query_db: AsyncSession, page_object: AreaBaseModel) -> bool:
        """
        校验用户名是否唯一service

        :param query_db: orm对象
        :param page_object: 用户对象
        :return: 校验结果
        """
        name = -1 if page_object.name is None else page_object.name
        model = await AreaDao.get_info_by_title(query_db, AreaBaseModel(name=page_object.name))
        if model and model.id == page_object.id:
            return CommonConstant.UNIQUE
        if model and model.name == name:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE
