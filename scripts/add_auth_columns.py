import os
import asyncio
import asyncpg
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.core.settings import settings

async def main():
    url = os.getenv('DATABASE_URL') or settings.database_url
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
        sql = '''
        ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts integer NOT NULL DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until timestamp with time zone NULL;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamp with time zone NULL;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip varchar NULL;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT now();
        '''
        await conn.execute(sql)
        print('Added missing auth columns (if they did not exist).')
    except Exception as e:
        print('execute error', e)
    finally:
        await conn.close()

asyncio.run(main())
