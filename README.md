# Платформа для стартапа HyperSpectRus

Приложение для съемки, обработки и анализа спектральных данных медицинских изображений

Приложение объединяет локальное устройство съемки (PyQt), сервер обработки (FastAPI) и веб-интерфейс (Vue.js) для комплексного анализа спектральных данных

Основные функции:

Локальное устройство сбора данных (PyQt):
- Захват изображений с камеры
- Управление светодиодами (Arduino)
- Предварительная обработка и сжатие снимков
- Отправка данных на сервер или локальное хранение

Сервер обработки и хранения (FastAPI):
- Прием снимков и сохранение в базе (PostgreSQL, S3).
- Обработка данных и анализ спектров (NumPy, SciPy).
- Асинхронная обработка в Celery + Redis.
- API для взаимодействия с веб-интерфейсом

Web-интерфейс (Vue.js):
- Админский режим (настройка спектров, управление пользователями)
- Пользовательский режим (анализ данных, просмотр снимков)
- Визуализация результатов (графики, отчеты, PDF/CSV)


В сервисе авторизации и сервисе бэкенда миграции выполняются в разных схемах базы данных

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

```
docker exec -it hyperspectrus-postgres psql -h localhost -U admin -d hyperspectrus
SET search_path TO auth_schema;
```

docker-compose -p hyperspectrus run migrations python -c "from back.src.db.postgres import Base; print(Base.metadata.tables.keys())"