import os
import asyncio
import asyncpg
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.core.settings import settings

async def main():
    url = os.getenv('DATABASE_URL') or settings.database_url
    # Convert sqlalchemy-style url to asyncpg dsn
    if url.startswith('postgresql+asyncpg://'):
        dsn = url.replace('postgresql+asyncpg://', 'postgresql://', 1)
    elif url.startswith('postgresql://'):
        dsn = url
    else:
        print('Not a Postgres URL:', url)
        return
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    try:
        conn = await asyncpg.connect(dsn, ssl=ssl_ctx, statement_cache_size=0)
    except Exception as e:
        print('connect error', e)
        return
    try:
        rows = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        if not rows:
            print('users table does not exist or has no columns')
        else:
            print('users table columns:')
            for r in rows:
                print(r['column_name'], r['data_type'])
    finally:
        await conn.close()

asyncio.run(main())
