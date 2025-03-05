#!/bin/sh

set -e

echo "Ожидание базы данных..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
done
echo "PostgreSQL доступен!"

echo "Применяем миграции..."
alembic upgrade head

echo "Запускаем сервис..."
exec python src/main.py