#!/bin/bash

AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/camera-app.desktop"
LXSESSION_AUTOSTART="$HOME/.config/lxsession/LXDE-pi/autostart"

APP_PATH="$HOME/hyperspectrus/src/run.py"
PYTHON="/usr/bin/python3"

enable_kiosk() {
    echo "🛠️ Включение kiosk-режима..."

    mkdir -p "$AUTOSTART_DIR"

    # Создание .desktop файла
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=CameraApp
Exec=$PYTHON $APP_PATH
X-GNOME-Autostart-enabled=true
EOF

    # Комментируем lxpanel и pcmanfm
    if [ -f "$LXSESSION_AUTOSTART" ]; then
        sed -i 's|^@lxpanel|#@lxpanel|' "$LXSESSION_AUTOSTART"
        sed -i 's|^@pcmanfm|#@pcmanfm|' "$LXSESSION_AUTOSTART"
    fi

    echo "✅ kiosk включен. Перезагрузка..."
    sleep 1
    sudo reboot
}

disable_kiosk() {
    echo "🛠️ Выключение kiosk-режима..."

    # Удаление .desktop файла
    rm -f "$DESKTOP_FILE"

    # Раскомментируем lxpanel и pcmanfm
    if [ -f "$LXSESSION_AUTOSTART" ]; then
        sed -i 's|^#@lxpanel|@lxpanel|' "$LXSESSION_AUTOSTART"
        sed -i 's|^#@pcmanfm|@pcmanfm|' "$LXSESSION_AUTOSTART"
    fi

    echo "❎ kiosk выключен. Перезагрузка..."
    sleep 1
    sudo reboot
}

status_kiosk() {
    echo -n "📟 kiosk статус: "
    if [ -f "$DESKTOP_FILE" ]; then
        echo "ВКЛЮЧЕН"
    else
        echo "ВЫКЛЮЧЕН"
    fi
}

case "$1" in
    enable)
        enable_kiosk
        ;;
    disable)
        disable_kiosk
        ;;
    status)
        status_kiosk
        ;;
    *)
        echo "Использование: $0 {enable|disable|status}"
        ;;
esac
