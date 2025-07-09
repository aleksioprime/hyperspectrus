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


# Запуск на сервере:

## Подготовка сервера

Установите сервер с ОС Ubuntu 22.04+

Выполните обновление пакетов:
```
sudo apt update && sudo apt upgrade -y
```

Установите Docker:
```
sudo apt update && sudo apt install -y docker.io
```

Установите Compose-плагин:
```
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
```

Проверьте установку
```
docker compose version
```

## Переменные окружения

Переменные окружения берутся из репозитория.

Для загрузки контейнеров в Docker Hub используется:
```
DOCKER_HUB_USERNAME=<логин пользователя Docker Hub>
DOCKER_HUB_ACCESS_TOKEN=<access-токен, который был выдан в DockerHub>
```

Для деплоя приложения из репозитория на сервер используется:
```
SERVER_HOST=<IP-адрес сервера>
SERVER_SSH_KEY=<Приватный ключ для подключения к серверу по SSH>
SERVER_USER=<Имя пользователя сервера>
```

Для сервиса создаётся переменная `ENV_VARS`, куда записываются все переменные из `.env.example`

## Добавление бесплатного SSL-сертификата

В контейнер фронтенда добавлен CertBot, с помощью которого происходит регистрация сертификата

Проверьте установку:
```
docker exec -it hyperspectrus-front certbot --version
```

Запустите CertBot для получения сертификатов
```
docker exec -it hyperspectrus-front certbot --nginx -d hyperspectrus.ru -d www.hyperspectrus.ru
ls -l /etc/letsencrypt/live/hyperspectrus.ru/
```

Добавьте автообновление сертификатов (каждые 90 дней). Для этого откройте crontab:
```
sudo crontab -e
```

Добавьте строку:
```
0 3 * * * docker exec hyperspectrus-front certbot renew --quiet && docker exec hyperspectrus-front nginx -s reload
```

В случае необхожимости можно удалить сертификаты:
```
docker exec -it hyperspectrus-front rm -rf /etc/letsencrypt/renewal/hyperspectrus.ru.conf
docker exec -it hyperspectrus-front rm -rf /etc/letsencrypt/live/hyperspectrus.ru
docker exec -it hyperspectrus-front rm -rf /etc/letsencrypt/archive/hyperspectrus.ru
```

Проверьте логи на сервере

```
docker compose -p empolimer logs
docker logs empolimer-nodered
```

Сделать ручные миграции на сервере:

```
docker exec -it empolimer-back alembic upgrade head
```

Добавье администратора на сервер

```
docker exec empolimer-back python scripts/create_superuser.py \
  --username superuser \
  --password 1qaz@WSX \
  --email admin@empolimer.ru
```