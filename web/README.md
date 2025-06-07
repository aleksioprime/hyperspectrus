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

Создание тестового пользователя в базе данных (логин: `abrown`, пароль: `1qaz@WSX`):
```shell
docker exec -it hyperspectrus-postgres \
  psql -h localhost -U admin -d hyperspectrus \
  -c "
WITH ins_role AS (
  INSERT INTO roles (id, name, description)
    VALUES ('2cc04908-4366-4134-a37b-1556119282ef', 'user', 'Обычный пользователь')
    ON CONFLICT (name) DO UPDATE SET description=EXCLUDED.description
    RETURNING id
), ins_user AS (
  INSERT INTO users (
    id, username, hashed_password, email, first_name, last_name, is_active, is_superuser
  )
    VALUES (
      '3761ec8e-477b-4e9c-96a9-c30fc0dba5cd', 'abrown', 'scrypt:32768:8:1\$CNDPB7dD0tkAZOjO\$dfff6730eab97967fa50eb6937073e6431bf4034b3303c36e2f49b8cd0759a8f03ae9d9c79c5794ea0e2e3e285a5106939e9bdb6b3874c6f2fde26245c4614b7', 'abrown@hyperspectrus.ru',
      'Alex', 'Brown', true, false
    )
    ON CONFLICT (username) DO UPDATE SET
      hashed_password=EXCLUDED.hashed_password,
      email=EXCLUDED.email,
      is_active=EXCLUDED.is_active,
      is_superuser=EXCLUDED.is_superuser
    RETURNING id
)
INSERT INTO user_roles (id, user_id, role_id)
SELECT gen_random_uuid(), u.id, r.id FROM ins_user u, ins_role r
ON CONFLICT DO NOTHING;
"
```

Удаление тестового пользователя из базы данных:

```shell
docker exec -it hyperspectrus-postgres \
  psql -h localhost -U admin -d hyperspectrus \
  -c "
DELETE FROM user_roles WHERE user_id = (SELECT id FROM users WHERE username='abrown');
DELETE FROM users WHERE username='abrown';
"
```
## Справочные команды:
```
docker exec -it hyperspectrus-postgres psql -h localhost -U admin -d hyperspectrus
SET search_path TO auth_schema;
```
```
docker-compose -p hyperspectrus run migrations python -c "from back.src.db.postgres import Base; print(Base.metadata.tables.keys())"
```