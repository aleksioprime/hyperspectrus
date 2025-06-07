"""Управление светодиодами Raspberry Pi"""

from gpiozero import LED, Button


class LedController:
    def __init__(self):
        self.leds = {
            470: LED("GPIO14"),
            660: LED("GPIO15"),
            700: LED("GPIO18"),
            810: LED("GPIO23"),
            850: LED("GPIO24"),
            900: LED("GPIO25"),
            940: LED("GPIO8"),
        }
        self.button = Button("GPIO20", pull_up=True)
        self.off_all()

    def on(self, wavelength):
        """Включить LED по длине волны, выключить остальные."""
        self.off_all()
        led = self.leds.get(wavelength)
        if led:
            led.on()

    def off(self, wavelength):
        led = self.leds.get(wavelength)
        if led:
            led.off()

    def off_all(self):
        for led in self.leds.values():
            led.off()
