# Веб-приложение

## Запуск для разработчика

Скачайте репозиторий:
```
git clone https://github.com/aleksioprime/hyperspectrus.git
cd hyperspectrus
```

Запустите сервис локально:
```
cd web
docker-compose -p hyperspectrus up -d --build
```

Если выходит ошибка `exec /usr/src/app/entrypoint.sh: permission denied`, то нужно вручную установить флаг выполнения для entrypoint.sh в локальной системе:
```
chmod +x backend/entrypoint.sh
chmod +x auth/entrypoint.sh
```

Создание миграциий:
```shell
docker exec -it hyperspectrus-backend alembic revision --autogenerate -m "init migration"
```

Применение миграции (при перезапуске сервиса делается автоматически):
```shell
docker exec -it hyperspectrus-backend alembic upgrade head
```

Создание суперпользователя:
```shell
docker-compose -p hyperspectrus exec backend python scripts/create_superuser.py \
  --username superuser \
  --password 1q2w3e \
  --email admin@hyperspectrus.ru
```


## Справочные команды:
```
docker exec -it hyperspectrus-postgres psql -h localhost -U admin -d hyperspectrus
SET search_path TO auth_schema;
```
```
docker-compose -p hyperspectrus run migrations python -c "from back.src.db.postgres import Base; print(Base.metadata.tables.keys())"
```