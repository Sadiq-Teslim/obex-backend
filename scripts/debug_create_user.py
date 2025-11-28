import asyncio
import sys
import os

# Ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

print('DEBUG: starting debug_create_user.py')
try:
    print('DEBUG: about to import create_user')
    from app.services.auth_service import create_user
    print('DEBUG: imported create_user')
except Exception:
    print('DEBUG: import failed')
    import traceback
    traceback.print_exc()
    raise


async def main():
    print('DEBUG: entering main')
    try:
        user = await create_user(
            username="alice",
            password="Secur3Passw0rd!",
            ip_address="127.0.0.1",
            path="/",
            port=1234,
        )
        print('DEBUG: Created user:', getattr(user, 'id', None), getattr(user, 'username', None))
    except Exception as e:
        print('DEBUG: exception in create_user')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
