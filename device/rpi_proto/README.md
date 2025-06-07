# Приложения для устройства съёмки

## Подготовка системного окружения

Обновите список пакетов и установите системные обновления:
```sh
sudo apt update
sudo apt upgrade -y
```

Перейдите в консольную панель настроек Raspberry Pi:
```sh
sudo raspi-config
```

Для включения сервера удалённого рабочего стола из главного меню перейдите в `Interfacing Options` → `VNC` и выберите `Enable`.

После всех настроек в главном меню выберите `Finish` и, если будет вопрос `Would you like to reboot now?`, нажмите на `Yes`

Чтобы заставить Raspberry Pi всегда считать, что к HDMI-порту подключён монитор (необходимо для VNC и для корректировки изображения на китайских мини-дисплеях), и настроить его, откройте файл:
```sh
sudo nano /boot/config.txt
```

Добавьте строки:
```
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
```

Сохраните изменения в файле и перезагрузите устройство:
```
sudo reboot
```

## Подготовка проекта

Скачайте проект:
```
wget https://github.com/aleksioprime/hyperspectrus/archive/refs/heads/main.zip
unzip main.zip
```

Перенесите в рабочую папку:
```
mkdir ~/hyperspectrus
mv hyperspectrus-main/device/rpi_proto/* ~/hyperspectrus/
```

Удалите скачанные файлы:
```
rm -rf ~/main.zip ~/hyperspectrus-main
```

Установите необходимые библиотеки:
```
pip install -r ~/hyperspectrus/requirements.txt
```

## Запуск проекта

### Ручной запуск (только на самой плате)

Подключитесь к рабочему столу через VNC, откройте терминал и запустите:
```
cd ~/hyperspectrus/src && python run.py
```

### Автоматический запуск в режиме KIOSK (можно по SSH)

Добавьте права на скрипт включения режима KIOSK:
```
chmod +x ~/hyperspectrus/kiosk.sh
```

Включение режима KIOSK:
```
~/hyperspectrus/kiosk.sh enable
```

Отключение режима KIOSK:
```
~/hyperspectrus/kiosk.sh disable
```

## Тестирование проекта

Тест подключения к локалному web-серверу приложения:

curl -X POST "http://localhost:8080

Тест создания задачи:
```
curl -X POST "http://localhost:8080/tasks" \
     -H "Content-Type: application/json" \
     -d '{
           "title": "Больная Кузьмина А.В.",
           "spectra": [470, 660, 810]
         }'
```