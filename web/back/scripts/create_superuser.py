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
    Создаёт или обновляет суперпользователя
    """
    default_first_name = "Администратор"
    default_last_name = "Администраторов"

    existing_user_query = await session.execute(
        select(User).filter((User.username == username) | (User.email == email))
    )
    existing_user = existing_user_query.scalars().first()

    if existing_user:
        if force:
            print(f"Обновляем данные суперпользователя {existing_user.username}...")
            existing_user.username = username
            existing_user.password = password
            existing_user.email = email
            existing_user.is_superuser = True
            await session.commit()
            print(f"Суперпользователь {existing_user.username} обновлён!")
        else:
            print(f"Суперпользователь {existing_user.username} уже существует. Используйте --force для обновления.")
        return

    superuser = User(
        username=username,
        email=email,
        password=password,
        is_superuser=True,
        first_name=default_first_name,
        last_name=default_last_name,
    )

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
