# Запуск программы на Raspberry Pi

Тестируемая конфигурация:

- Микрокомпьютер: Raspberry Pi 3 B+
- Камера: USB HD-камера 2MP CMOS OV2710 1080P
- Экран: сенсорный экран Waveshare 3.5inch RPi LCD (C)
- Операционная система: Raspberry PI OS (Legacy, 32-bit) - Debian Bullseye

Справочная информация:

- https://www.waveshare.com/wiki/3.5inch_RPi_LCD_(C)
- https://www.waveshare.com/wiki/3.5inch_RPi_LCD_(C)_Manual_Configuration


## Подготовка окружения (можно через SSH)

Установите и запустите драйвера для LCD:
```
git clone https://github.com/waveshare/LCD-show.git
cd LCD-show/
chmod +x LCD35C-show
./LCD35C-show 180
```

Для поворота экрана откройте файл настроек:
```
sudo nano /boot/config.txt
```
Измените строку:
```
...
dtoverlay=waveshare35c:rotate=270
...
```

Установите библиотеку OpenCV:
```
sudo apt install libopenblas0 libatlas-base-dev
pip install opencv-python==4.11.0.86
pip install pillow==11.2.1
```

Установите библиотеку PyQT:
```
sudo apt install qtbase5-dev qt5-qmake
pip install pyqt5 --only-binary=:all:
```

## Запуск программы

Скопируйте проект:
```
wget https://github.com/aleksioprime/hyperspectrus/archive/refs/heads/main.zip
unzip main.zip
mkdir ~/hyperspectrus
mv hyperspectrus-main/device/rpi/* ~/hyperspectrus/
chmod +x ~/hyperspectrus/kiosk.sh
```

Удаление скачанных файлов:
```
rm -rf ~/main.zip ~/hyperspectrus-main
```

Включение режима KIOSK:
```
./hyperspectrus/kiosk.sh enable
```

Отключение режима KIOSK:
```
./hyperspectrus/kiosk.sh disable
```

## Ручная настройка автозапуска:

Создайте файл для автозапуска:
```
mkdir -p ~/.config/autostart
nano ~/.config/autostart/camera-app.desktop
```

Содержимое файла:
```
[Desktop Entry]
Type=Application
Name=CameraApp
Exec=/usr/bin/python3 /home/pi/hyperspectrus/src/run.py
X-GNOME-Autostart-enabled=true
```

Уберите системную панель и рабочий стол.
Откройте файл:
```
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart
```

Запишите следующие строки:
```
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0
```

Для включения рабочего стола нужно добавить эти строки (для выключение - закомментировать #):
```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
```