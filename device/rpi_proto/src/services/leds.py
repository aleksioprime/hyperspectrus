"""Управление светодиодами Raspberry Pi без использования Arduino.

Модуль предоставляет простой контроллер из семи светодиодов и кнопки.
При нажатии кнопки поочерёдно зажигается заданный светодиод.
"""

from gpiozero import LED, Button
from time import sleep


class LedController:
    """Контроллер управления семью светодиодами и кнопкой."""

    def __init__(self):
        """Настраивает светодиоды и кнопку GPIO."""
        # Создаём объекты для светодиодов (настройте номера пинов при необходимости)
        self.leds = [
            LED("GPIO14"),  # 470 нм
            LED("GPIO15"),  # 660 нм
            LED("GPIO18"),  # 700 нм
            LED("GPIO23"),  # 810 нм
            LED("GPIO24"),  # 850 нм
            LED("GPIO25"),  # 900 нм
            LED("GPIO8"),   # 940 нм
        ]
        # Кнопка запуска подсветки
        self.button = Button("GPIO7", pull_up=True)
        # Гасим все светодиоды при старте
        for led in self.leds:
            led.off()

    def cycle_led(self, index: int):
        """Зажигает светодиод по индексу с ожиданием нажатий кнопки."""
        led = self.leds[index]
        self.button.wait_for_press()
        led.on()
        sleep(1)
        self.button.wait_for_press()
        led.off()
        sleep(1)
