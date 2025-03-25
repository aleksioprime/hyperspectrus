import argparse
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from src.models.user import User, Role
from src.db.postgres import async_session_maker


async def create_or_update_superuser(session: AsyncSession, username: str, password: str, email: str, force: bool):
    """
    Создаёт или обновляет суперпользователя.
    """
    # Загружаем пользователя вместе с ролями
    existing_user_query = await session.execute(
        select(User).options(joinedload(User.roles)).filter((User.username == username) | (User.email == email))
    )
    existing_user = existing_user_query.scalars().first()

    if existing_user:
        if force:
            print(f"Обновляем данные суперпользователя {existing_user.username}...")
            existing_user.password = password
            existing_user.email = email
            existing_user.is_superuser = True

            # Получаем или создаем роль "admin"
            role_query = await session.execute(select(Role).filter_by(name="admin"))
            admin_role = role_query.scalars().first()

            if not admin_role:
                admin_role = Role(name="admin", description="Administrator role")
                session.add(admin_role)
                await session.flush()

            # Проверяем, есть ли у пользователя эта роль
            if admin_role not in existing_user.roles:
                existing_user.roles.append(admin_role)

            await session.commit()
            print(f"Суперпользователь {existing_user.username} обновлён!")
            return
        else:
            print(f"Суперпользователь {existing_user.username} уже существует. Используйте `--force`, чтобы обновить данные.")
            return

    # Создаём нового суперпользователя
    superuser = User(
        username=username,
        email=email,
        password=password,
        is_superuser=True
    )

    # Получаем или создаем роль "admin"
    role_query = await session.execute(select(Role).filter_by(name="admin"))
    admin_role = role_query.scalars().first()

    if not admin_role:
        admin_role = Role(name="admin", description="Administrator role")
        session.add(admin_role)
        await session.flush()

    # Назначаем роль суперпользователю
    superuser.roles.append(admin_role)
    session.add(superuser)

    try:
        await session.commit()
        print(f"Суперпользователь {username} успешно создан!")
    except IntegrityError as exc:
        await session.rollback()
        print(f"Ошибка при создании суперпользователя: {exc.orig}")


async def main():
    parser = argparse.ArgumentParser(description="Создание/обновление суперпользователя")
    parser.add_argument("--username", required=True, help="Логин суперпользователя")
    parser.add_argument("--password", required=True, help="Пароль суперпользователя")
    parser.add_argument("--email", required=True, help="E-mail суперпользователя")
    parser.add_argument("--force", action="store_true", help="Обновить данные, если суперпользователь уже существует")

    args = parser.parse_args()

    async with async_session_maker() as session:
        await create_or_update_superuser(session, args.username, args.password, args.email, args.force)


if __name__ == "__main__":
    asyncio.run(main())
