from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update,delete, desc

from module_personnel.util.file_utils import delete_file
from typing import Any
from module_personnel.entity.do.file_do import OaFile
from module_personnel.entity.vo.file_vo import OaFileBaseModel


class FileDAO(AsyncSession):
    @classmethod
    async def add_profiles(cls, db: AsyncSession, profiles: list[OaFile]) -> Any:
        """
        创建文件
        """
        db.add_all(profiles)
        await db.commit()

        for profile in profiles:
            await db.refresh(profile)
        return profiles

    @classmethod
    async def get_file_by_id(cls, id: int, db: AsyncSession) -> Any:
        """
        查询文件
        """
        result = await db.execute(select(OaFile).filter(OaFile.id == id))
        return result.scalars().first()

    @classmethod
    async def get_files(cls, db: AsyncSession, ids: list) -> list[OaFile]:
        query = (select(
            OaFile.name.label('name'),
            OaFile.filename.label('file_name'),
            OaFile.filepath.label('file_path'),
            OaFile.filesize.label('file_size'),
            OaFile.fileext.label('file_ext'),
            OaFile.mimetype.label('file_mime'))
                 .where(OaFile.id.in_(ids))
                 .order_by(desc(OaFile.id)))
        result = await db.execute(query)
        return result.mappings().all()

    @classmethod
    async def get_file_by_ids(cls, ids: str, db: AsyncSession) -> Any:
        """
        查询文件
        """
        ids = ids.split(',')
        result = await db.execute(select(OaFile).filter(OaFile.id.in_(ids)))
        return result.scalars().all()

    @classmethod
    async def delete_file(cls, id: int, db: AsyncSession) -> Any:
        """
        删除文件
        """
        file_result = await cls.get_file_by_id(id, db)
        if file_result:
            await delete_file(file_result.filepath)
        await db.execute(delete(OaFile).where(OaFile.id == id))
        result = await db.commit()
        return result

    @classmethod
    async def rename_file(cls, db: AsyncSession, query: OaFileBaseModel) -> OaFile:
        await db.execute(update(OaFile).values(name = query.name).where(OaFile.id == query.id))
        result = await db.commit()
        return result