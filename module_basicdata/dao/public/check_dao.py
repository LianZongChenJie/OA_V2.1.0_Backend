from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class CheckDao:
    @classmethod
    async def execute_row_sql(cls, db: AsyncSession, sql: str, params: dict) -> dict:
        """
        执行sql语句，返回结果集
        :param db:
        :param sql:
        :param params:
        :return: 返回单调数据
        """
        sql = text(sql)
        result = await db.execute(sql, params)
        return result.mappings().first()

    @classmethod
    async def execute_list_sql(cls, db: AsyncSession, sql: str, params: dict) -> list:
        """
        执行sql语句，返回结果集
        :param db:
        :param sql:
        :param params:
        :return: list数据
        """
        sql = text(sql)
        result = await db.execute(sql, params)
        return result.mappings().all()

    @classmethod
    async def execute_update_sql(cls, db: AsyncSession, sql: str, params: dict) -> bool:
        """
        执行sql语句，返回结果集
        :param db:
        :param sql:
        :param params:
        :return: bool数据
        """
        try:
            sql = text(sql)
            await db.execute(sql, params)
            await db.commit()
            return True
        except Exception as e:
            raise e
            return False