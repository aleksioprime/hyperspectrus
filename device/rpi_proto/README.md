# Приложения для устройства съёмки

## Запуск программы на Raspberry Pi

Обновите пакеты:
```sh
sudo apt update
sudo apt upgrade -y
```

Перейдите в панель настроек:
```sh
sudo raspi-config
```

- Из главного меню перейдите в `Interfacing Options` → `VNC` и выберите `Enable`
- Из главного меню перейдите в `Interfacing Options` → `Legacy Camera` и выберите `Enable`
- В главном меню выберите `Finish` и после вопроса `Would you like to reboot now?` нажмите на `Yes`

Если изображение сместилось на экране, откройте файл конфигурации:
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

Сохраните изменения в файле
