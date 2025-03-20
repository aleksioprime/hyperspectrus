from logging.config import fileConfig
# Подключаем асинхронный движок SQLAlchemy
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool
# Подключаем Alembic
from alembic import context

# Загружаем настройки из проекта (например, URL базы данных)
from src.core.config import settings
# Импортируем базовый класс моделей (чтобы Alembic знал о таблицах)

from src.db.postgres import Base
from src.models.user import User, Organization
from src.models.role import Role


# Загружаем конфигурацию Alembic
config = context.config

# Берем текущий раздел конфигурации (обычно `[alembic]` в `alembic.ini`)
section = config.config_ini_section
# Устанавливаем URL базы данных для Alembic, используя значение из `settings.db.dsn`
config.set_section_option(section, 'ALEMBIC_URL', settings.db.dsn)

# Включаем логирование Alembic, если файл конфигурации указан
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Указываем Alembic, где искать метаданные моделей
# Это нужно, чтобы Alembic мог отслеживать изменения в структурах таблиц

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запуск миграций в оффлайн-режиме (без подключения к базе данных).

    В этом режиме Alembic просто генерирует SQL-файл с изменениями,
    но не применяет их к реальной БД.
    """
    url = config.get_main_option("sqlalchemy.url")  # Получаем URL базы данных
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Подставляет значения параметров прямо в SQL-запрос
    )

    # Начинаем транзакцию и выполняем миграции
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """
    Запускает миграции в указанном соединении к базе данных (синхронно)
    """

    # Конфигурируем Alembic с текущим соединением и метаданными моделей
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        )

    # Начинаем транзакцию и применяем миграции
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Запуск миграций в онлайн-режиме (с подключением к базе данных).
    В этом режиме Alembic подключается к базе и применяет миграции сразу.
    """
    # Создаем асинхронный движок для работы с БД
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",  # Используем параметры, начинающиеся с "sqlalchemy."
        poolclass=pool.NullPool,  # Отключаем пул соединений (каждый запрос — новое соединение)
    )

    # Подключаемся к базе и запускаем миграции
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


# Проверяем, в каком режиме работает Alembic (offline или online)
if context.is_offline_mode():
    # Если оффлайн, просто генерируем SQL-команды
    run_migrations_offline()
else:
    # Если онлайн, подключаемся к базе и применяем миграции
    import asyncio
    asyncio.run(run_migrations_online())
