### Автоматический запуск сервера при старте Raspberry

Скопируйте сервер на Raspberry:
```

```

Создаём systemd-сервис:

```bash
sudo nano /etc/systemd/system/autoupdate.service
```

Добавляем в файл:

```ini
[Unit]
Description=Автообновление прошивки
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/autoupdate_server.py
WorkingDirectory=/home/pi/
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Активируем сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable autoupdate.service
sudo systemctl start autoupdate.service
```