from datetime import datetime
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.rewards_cate_dao import RewardsCateDao
from module_admin.entity.vo.rewards_cate_vo import (
    AddRewardsCateModel,
    DeleteRewardsCateModel,
    EditRewardsCateModel,
    RewardsCateModel,
    RewardsCatePageQueryModel,
)
from utils.common_util import CamelCaseUtil


class RewardsCateService:
    """
    奖罚项目管理模块服务层
    """

    @classmethod
    async def get_rewards_cate_list_services(
            cls, query_db: AsyncSession, query_object: RewardsCatePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取奖罚项目列表信息 service

        :param query_db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 奖罚项目列表信息对象
        """
        rewards_cate_list_result = await RewardsCateDao.get_rewards_cate_list(query_db, query_object, is_page)

        return rewards_cate_list_result

    @classmethod
    async def check_rewards_cate_title_unique_services(
            cls, query_db: AsyncSession, page_object: RewardsCateModel
    ) -> bool:
        """
        校验奖罚项目名称是否唯一 service

        :param query_db: orm 对象
        :param page_object: 奖罚项目对象
        :return: 校验结果
        """
        rewards_cate_id = -1 if page_object.id is None else page_object.id
        rewards_cate = await RewardsCateDao.get_rewards_cate_detail_by_info(query_db, page_object)
        if rewards_cate and rewards_cate.id != rewards_cate_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def add_rewards_cate_services(
        cls, request: Request, query_db: AsyncSession, page_object: AddRewardsCateModel
    ) -> CrudResponseModel:
        """
        新增奖罚项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 新增奖罚项目对象
        :return: 新增奖罚项目校验结果
        """
        if not await cls.check_rewards_cate_title_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增奖罚项目{page_object.title}失败，奖罚项目名称已存在')
        
        try:
            current_time = int(datetime.now().timestamp())
            add_rewards_cate = RewardsCateModel(
                title=page_object.title,
                status=page_object.status if page_object.status is not None else 1,
                create_time=current_time,
                update_time=current_time
            )
            await RewardsCateDao.add_rewards_cate_dao(query_db, add_rewards_cate)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_rewards_cate_services(
        cls, request: Request, query_db: AsyncSession, page_object: EditRewardsCateModel
    ) -> CrudResponseModel:
        """
        编辑奖罚项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 编辑奖罚项目对象
        :return: 编辑奖罚项目校验结果
        """
        edit_rewards_cate = page_object.model_dump(exclude_unset=True)
        rewards_cate_info = await cls.rewards_cate_detail_services(query_db, page_object.id)
        
        if rewards_cate_info.id:
            if not await cls.check_rewards_cate_title_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改奖罚项目{page_object.title}失败，奖罚项目名称已存在')
            
            try:
                edit_rewards_cate['update_time'] = int(datetime.now().timestamp())
                await RewardsCateDao.edit_rewards_cate_dao(query_db, edit_rewards_cate)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='奖罚项目不存在')

    @classmethod
    async def delete_rewards_cate_services(
        cls, request: Request, query_db: AsyncSession, page_object: DeleteRewardsCateModel
    ) -> CrudResponseModel:
        """
        删除奖罚项目信息 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 删除奖罚项目对象
        :return: 删除奖罚项目校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for rewards_cate_id in id_list:
                    rewards_cate = await cls.rewards_cate_detail_services(query_db, int(rewards_cate_id))
                    if not rewards_cate.id:
                        raise ServiceException(message='奖罚项目不存在')
                    
                    update_time = int(datetime.now().timestamp())
                    await RewardsCateDao.delete_rewards_cate_dao(
                        query_db, 
                        RewardsCateModel(id=int(rewards_cate_id), update_time=update_time)
                    )
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入奖罚项目 id 为空')

    @classmethod
    async def set_rewards_cate_status_services(
        cls, request: Request, query_db: AsyncSession, page_object: EditRewardsCateModel
    ) -> CrudResponseModel:
        """
        设置奖罚项目状态 service

        :param request: Request 对象
        :param query_db: orm 对象
        :param page_object: 设置奖罚项目状态对象
        :return: 设置奖罚项目状态校验结果
        """
        rewards_cate_info = await cls.rewards_cate_detail_services(query_db, page_object.id)
        
        if rewards_cate_info.id:
            try:
                update_time = int(datetime.now().timestamp())
                
                if page_object.status == 0:
                    await RewardsCateDao.disable_rewards_cate_dao(
                        query_db, 
                        RewardsCateModel(id=page_object.id, update_time=update_time)
                    )
                elif page_object.status == 1:
                    await RewardsCateDao.enable_rewards_cate_dao(
                        query_db, 
                        RewardsCateModel(id=page_object.id, update_time=update_time)
                    )
                
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='操作成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='奖罚项目不存在')

    @classmethod
    async def rewards_cate_detail_services(cls, query_db: AsyncSession, rewards_cate_id: int) -> RewardsCateModel:
        """
        获取奖罚项目详细信息 service

        :param query_db: orm 对象
        :param rewards_cate_id: 奖罚项目 id
        :return: 奖罚项目 id 对应的信息
        """
        rewards_cate = await RewardsCateDao.get_rewards_cate_detail_by_id(query_db, rewards_cate_id)
        result = RewardsCateModel(**CamelCaseUtil.transform_result(rewards_cate)) if rewards_cate else RewardsCateModel()

        return result
