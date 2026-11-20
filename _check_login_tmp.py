import asyncio
import time

from dotenv import load_dotenv

load_dotenv('.env.dev')


async def main():
    # 1. bcrypt 密码校验耗时
    import bcrypt
    hashed = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
    t = time.perf_counter()
    for _ in range(3):
        bcrypt.checkpw(b'admin123', hashed.encode('utf-8'))
    print('bcrypt checkpw x3: %.3fs' % (time.perf_counter() - t))

    # 2. 数据库查询耗时
    from config.database import create_async_db_engine, create_async_session_local
    from module_admin.dao.login_dao import login_by_account
    engine = create_async_db_engine(echo=False)
    Session = create_async_session_local(engine)
    async with Session() as db:
        t = time.perf_counter()
        user = await login_by_account(db, 'admin')
        print('login_by_account: %.3fs' % (time.perf_counter() - t), bool(user))

    # 3. Redis 连接与读写耗时
    import redis
    t = time.perf_counter()
    r = redis.Redis(host='127.0.0.1', port=6379, db=0, socket_connect_timeout=5)
    try:
        r.get('test:login:timing')
        print('redis sync get: %.3fs' % (time.perf_counter() - t), r.ping())
    except Exception as e:
        print('redis ERROR: %.3fs' % (time.perf_counter() - t), e)

    # 4. IP 归属地查询耗时（含外部 httpx）
    from common.annotation.log_annotation import get_ip_location
    t = time.perf_counter()
    loc = await get_ip_location('211.149.169.81')
    print('get_ip_location (1st): %.3fs' % (time.perf_counter() - t), loc)
    t = time.perf_counter()
    loc = await get_ip_location('211.149.169.81')
    print('get_ip_location (cached): %.3fs' % (time.perf_counter() - t), loc)

    await engine.dispose()


asyncio.run(main())
