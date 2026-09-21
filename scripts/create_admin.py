"""
Run once per new admin account: python scripts/create_admin.py
Prompts for details, inserts directly into admin_users. This is the ONLY
way an admin account is ever created — there is no public registration
endpoint for admins, by design.
"""
import asyncio
import sys
import os
import getpass

# Same import layout as production (`uvicorn main:app --app-dir app`).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from core.db import AsyncSessionLocal
from core.security import hash_password
from models.user import AdminUser


async def main():
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    async with AsyncSessionLocal() as db:
        admin = AdminUser(full_name=full_name, email=email, password_hash=hash_password(password))
        db.add(admin)
        await db.commit()
        print(f"Created admin account: {email}")


if __name__ == "__main__":
    asyncio.run(main())
