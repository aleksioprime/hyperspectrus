# Приложение для рабочего компьютера

## Установка pyenv

Убедитесь, что в pyenv установлена нужная версия Python
```
pyenv versions
```

Выберите нужную версию Python для текущей папки
```
pyenv local 3.12.10
```

Установите Poetry:
```
poetry install
```

## Запуск приложения
```
PYTHONPATH=src poetry run python src/main.py
```
