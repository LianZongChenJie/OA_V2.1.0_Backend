from datetime import datetime
from typing import Any

from sqlalchemy import and_, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_admin.entity.do.car_do import OaCar, OaCarRepair, OaCarFee, OaCarMileage
from module_admin.entity.vo.car_vo import (
    CarPageQueryModel,
    CarRepairPageQueryModel,
    CarFeePageQueryModel,
    CarMileagePageQueryModel,
)
from utils.page_util import PageUtil


class CarDao:
    """
    车辆管理模块数据库操作层
    """

    @classmethod
    async def get_car_detail_by_id(cls, db: AsyncSession, car_id: int) -> OaCar | None:
        """
        根据车辆 ID 获取车辆详细信息

        :param db: orm 对象
        :param car_id: 车辆 ID
        :return: 车辆信息对象
        """
        car_info = (
            (await db.execute(select(OaCar).where(OaCar.id == car_id)))
            .scalars()
            .first()
        )

        return car_info

    @classmethod
    async def get_car_list(
            cls, db: AsyncSession, query_object: CarPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取车辆列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 车辆列表信息对象
        """
        from module_admin.entity.do.user_do import SysUser
        
        query = (
            select(OaCar, SysUser.nick_name.label('driver_name'))
            .join(SysUser, SysUser.user_id == OaCar.driver, isouter=True)
            .where(OaCar.delete_time == 0)
        )
        
        # 关键词搜索：同时搜索车辆名称和车牌号码
        if query_object.keywords:
            query = query.where(
                or_(
                    OaCar.title.like(f'%{query_object.keywords}%'),
                    OaCar.name.like(f'%{query_object.keywords}%'),
                )
            )
        
        query = query.order_by(OaCar.id.desc())
        
        car_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return car_list

    @classmethod
    async def add_car_dao(cls, db: AsyncSession, car: dict) -> OaCar:
        """
        新增车辆数据库操作

        :param db: orm 对象
        :param car: 车辆字典
        :return:
        """
        # 排除关联查询字段，只保留数据库表中存在的字段
        db_car_data = {
            k: v for k, v in car.items() 
            if k not in ['driver_name']
        }
        db_car = OaCar(**db_car_data)
        db.add(db_car)
        await db.flush()

        return db_car

    @classmethod
    async def edit_car_dao(cls, db: AsyncSession, car: dict) -> None:
        """
        编辑车辆数据库操作

        :param db: orm 对象
        :param car: 需要更新的车辆字典
        :return:
        """
        # 排除关联查询字段，只保留数据库表中存在的字段
        db_car_data = {
            k: v for k, v in car.items() 
            if k not in ['driver_name']
        }
        await db.execute(update(OaCar), [db_car_data])

    @classmethod
    async def delete_car_dao(cls, db: AsyncSession, car_id: int) -> None:
        """
        删除车辆数据库操作（逻辑删除）

        :param db: orm 对象
        :param car_id: 车辆 ID
        :return:
        """
        await db.execute(
            update(OaCar)
            .where(OaCar.id == car_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )


class CarRepairDao:
    """
    车辆维修/保养记录模块数据库操作层
    """

    @classmethod
    async def get_car_repair_detail_by_id(cls, db: AsyncSession, repair_id: int) -> OaCarRepair | None:
        """
        根据记录 ID 获取维修/保养记录详细信息

        :param db: orm 对象
        :param repair_id: 记录 ID
        :return: 记录信息对象
        """
        repair_info = (
            (await db.execute(select(OaCarRepair).where(OaCarRepair.id == repair_id)))
            .scalars()
            .first()
        )

        return repair_info

    @classmethod
    async def get_car_repair_list(
            cls, db: AsyncSession, query_object: CarRepairPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取维修/保养记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 维修/保养记录列表信息对象
        """
        from module_admin.entity.do.car_do import OaCar
        from module_admin.entity.do.user_do import SysUser

        query = (
            select(OaCarRepair, OaCar.title.label('car_name'), SysUser.nick_name.label('handled_name'))
            .join(OaCar, OaCar.id == OaCarRepair.car_id, isouter=True)
            .join(SysUser, SysUser.user_id == OaCarRepair.handled, isouter=True)
            .where(OaCarRepair.delete_time == 0)
        )

        # 按类型筛选
        if query_object.types:
            query = query.where(OaCarRepair.types == query_object.types)

        # 关键词搜索
        if query_object.keywords:
            query = query.where(OaCar.title.like(f'%{query_object.keywords}%'))

        # 时间范围查询
        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    begin_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1]).timestamp())
                    query = query.where(
                        and_(
                            OaCarRepair.repair_time >= begin_timestamp,
                            OaCarRepair.repair_time <= end_timestamp,
                            )
                    )
            except ValueError:
                pass

        query = query.order_by(OaCarRepair.id.desc())

        repair_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return repair_list

    @classmethod
    async def add_car_repair_dao(cls, db: AsyncSession, repair: dict) -> OaCarRepair:
        """
        新增维修/保养记录数据库操作

        :param db: orm 对象
        :param repair: 维修/保养记录字典
        :return:
        """
        # 排除关联查询字段
        db_repair_data = {
            k: v for k, v in repair.items()
            if k not in ['car_name', 'handled_name']
        }
        db_repair = OaCarRepair(**db_repair_data)
        db.add(db_repair)
        await db.flush()

        return db_repair

    @classmethod
    async def edit_car_repair_dao(cls, db: AsyncSession, repair: dict) -> None:
        """
        编辑维修/保养记录数据库操作

        :param db: orm 对象
        :param repair: 需要更新的维修/保养记录字典
        :return:
        """
        # 排除关联查询字段
        db_repair_data = {
            k: v for k, v in repair.items()
            if k not in ['car_name', 'handled_name']
        }
        await db.execute(update(OaCarRepair), [db_repair_data])

    @classmethod
    async def delete_car_repair_dao(cls, db: AsyncSession, repair_id: int) -> None:
        """
        删除维修/保养记录数据库操作（逻辑删除）

        :param db: orm 对象
        :param repair_id: 记录 ID
        :return:
        """
        await db.execute(
            update(OaCarRepair)
            .where(OaCarRepair.id == repair_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )


class CarFeeDao:
    """
    车辆费用记录模块数据库操作层
    """

    @classmethod
    async def get_car_fee_detail_by_id(cls, db: AsyncSession, fee_id: int) -> OaCarFee | None:
        """
        根据费用 ID 获取费用详细信息

        :param db: orm 对象
        :param fee_id: 费用 ID
        :return: 费用信息对象
        """
        fee_info = (
            (await db.execute(select(OaCarFee).where(OaCarFee.id == fee_id)))
            .scalars()
            .first()
        )

        return fee_info

    @classmethod
    async def get_car_fee_list(
            cls, db: AsyncSession, query_object: CarFeePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取费用记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 费用记录列表信息对象
        """
        from module_admin.entity.do.car_do import OaCar
        from module_admin.entity.do.user_do import SysUser
        from module_admin.entity.do.basic_adm_do import OaBasicAdm

        query = (
            select(OaCarFee, OaCar.title.label('car_name'), SysUser.nick_name.label('handled_name'), OaBasicAdm.title.label('types_str'))
            .join(OaCar, OaCar.id == OaCarFee.car_id, isouter=True)
            .join(SysUser, SysUser.user_id == OaCarFee.handled, isouter=True)
            .join(OaBasicAdm, OaBasicAdm.id == OaCarFee.types, isouter=True)
            .where(OaCarFee.delete_time == 0)
        )

        # 按类型筛选
        if query_object.types:
            query = query.where(OaCarFee.types == query_object.types)

        # 关键词搜索
        if query_object.keywords:
            query = query.where(
                or_(
                    OaCarFee.title.like(f'%{query_object.keywords}%'),
                    OaCar.title.like(f'%{query_object.keywords}%'),
                )
            )

        # 时间范围查询
        if query_object.diff_time:
            try:
                time_range = query_object.diff_time.split('~')
                if len(time_range) == 2:
                    begin_timestamp = int(datetime.fromisoformat(time_range[0]).timestamp())
                    end_timestamp = int(datetime.fromisoformat(time_range[1]).timestamp())
                    query = query.where(
                        and_(
                            OaCarFee.fee_time >= begin_timestamp,
                            OaCarFee.fee_time <= end_timestamp,
                            )
                    )
            except ValueError:
                pass

        query = query.order_by(OaCarFee.id.desc())

        fee_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return fee_list

    @classmethod
    async def add_car_fee_dao(cls, db: AsyncSession, fee: dict) -> OaCarFee:
        """
        新增费用记录数据库操作

        :param db: orm 对象
        :param fee: 费用记录字典
        :return:
        """
        db_fee = OaCarFee(**fee)
        db.add(db_fee)
        await db.flush()

        return db_fee

    @classmethod
    async def edit_car_fee_dao(cls, db: AsyncSession, fee: dict) -> None:
        """
        编辑费用记录数据库操作

        :param db: orm 对象
        :param fee: 需要更新的费用记录字典
        :return:
        """
        await db.execute(update(OaCarFee), [fee])

    @classmethod
    async def delete_car_fee_dao(cls, db: AsyncSession, fee_id: int) -> None:
        """
        删除费用记录数据库操作（逻辑删除）

        :param db: orm 对象
        :param fee_id: 费用 ID
        :return:
        """
        await db.execute(
            update(OaCarFee)
            .where(OaCarFee.id == fee_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )


class CarMileageDao:
    """
    车辆里程记录模块数据库操作层
    """

    @classmethod
    async def get_car_mileage_detail_by_id(cls, db: AsyncSession, mileage_id: int) -> OaCarMileage | None:
        """
        根据里程 ID 获取里程详细信息

        :param db: orm 对象
        :param mileage_id: 里程 ID
        :return: 里程信息对象
        """
        mileage_info = (
            (await db.execute(select(OaCarMileage).where(OaCarMileage.id == mileage_id)))
            .scalars()
            .first()
        )

        return mileage_info

    @classmethod
    async def get_car_mileage_list(
            cls, db: AsyncSession, query_object: CarMileagePageQueryModel, car_id: int, is_page: bool = False
    ) -> PageModel | list[dict]:
        """
        根据查询参数获取里程记录列表信息

        :param db: orm 对象
        :param query_object: 查询参数对象
        :param car_id: 车辆 ID
        :param is_page: 是否开启分页
        :return: 里程记录列表信息对象
        """
        query = (
            select(OaCarMileage)
            .where(OaCarMileage.car_id == car_id, OaCarMileage.delete_time == 0)
        )

        query = query.order_by(OaCarMileage.mileage_time.desc())

        mileage_list: PageModel | list[dict] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return mileage_list

    @classmethod
    async def get_latest_mileage(cls, db: AsyncSession, car_id: int) -> float | None:
        """
        获取车辆最新里程数

        :param db: orm 对象
        :param car_id: 车辆 ID
        :return: 最新里程数
        """
        result = await db.execute(
            select(OaCarMileage.mileage)
            .where(OaCarMileage.car_id == car_id, OaCarMileage.delete_time == 0)
            .order_by(OaCarMileage.mileage_time.desc())
        )
        mileage = result.scalar()

        return float(mileage) if mileage else None

    @classmethod
    async def add_car_mileage_dao(cls, db: AsyncSession, mileage: dict) -> OaCarMileage:
        """
        新增里程记录数据库操作

        :param db: orm 对象
        :param mileage: 里程记录字典
        :return:
        """
        db_mileage = OaCarMileage(**mileage)
        db.add(db_mileage)
        await db.flush()

        return db_mileage

    @classmethod
    async def edit_car_mileage_dao(cls, db: AsyncSession, mileage: dict) -> None:
        """
        编辑里程记录数据库操作

        :param db: orm 对象
        :param mileage: 需要更新的里程记录字典
        :return:
        """
        await db.execute(update(OaCarMileage), [mileage])

    @classmethod
    async def delete_car_mileage_dao(cls, db: AsyncSession, mileage_id: int) -> None:
        """
        删除里程记录数据库操作（逻辑删除）

        :param db: orm 对象
        :param mileage_id: 里程 ID
        :return:
        """
        await db.execute(
            update(OaCarMileage)
            .where(OaCarMileage.id == mileage_id)
            .values(delete_time=int(datetime.now().timestamp()))
        )
