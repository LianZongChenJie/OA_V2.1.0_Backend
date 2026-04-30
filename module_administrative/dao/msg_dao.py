from sqlalchemy.ext.asyncio import AsyncSession
from module_administrative.entity.do.msg_do import OaMsg

class MsgDao:
    @classmethod
    async def add_list(cls, db: AsyncSession, msg_list: list[OaMsg]):
        for msg in msg_list:
            db.add(msg)
        result = await db.commit()
        return result
