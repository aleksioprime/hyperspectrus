import cv2
from gpiozero import LED
from picamera2 import Picamera2

# === Настройка GPIO-светодиодов по длинам волн ===
LED_PINS = {
    520: LED("GPIO8"),
    660: LED("GPIO25"),
    700: LED("GPIO24"),
    810: LED("GPIO12"),
    850: LED("GPIO18"),
    900: LED("GPIO15"),
    940: LED("GPIO14"),
}

# Добавим OFF как первую опцию (index 0)
WAVELENGTHS = [None, 520, 660, 700, 810, 850, 900, 940]  # index 0 = OFF

# === Инициализация камеры ===
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 200)}))
picam2.start()

cv2.namedWindow("Camera", cv2.WINDOW_AUTOSIZE)

# === Слайдеры ===
def nothing(x): pass

def update_led(val):
    """Включает один светодиод по индексу или выключает все (OFF)."""
    selected = WAVELENGTHS[val]
    for wl, led in LED_PINS.items():
        led.on() if wl == selected else led.off()

cv2.createTrackbar("Exposure (us)", "Camera", 1000, 20000, nothing)
cv2.createTrackbar("Gain x10", "Camera", 10, 40, nothing)
cv2.createTrackbar("LED λ (index)", "Camera", 0, len(WAVELENGTHS) - 1, update_led)

# === Главный цикл ===
while True:
    # Получаем значения с трекбаров
    exp = cv2.getTrackbarPos("Exposure (us)", "Camera")
    gain = cv2.getTrackbarPos("Gain x10", "Camera") / 10.0
    idx = cv2.getTrackbarPos("LED λ (index)", "Camera")
    selected_wl = WAVELENGTHS[idx]

    # Обновляем параметры камеры
    picam2.set_controls({
        "AeEnable": False,
        "ExposureTime": exp,
        "AnalogueGain": gain,
    })

    # Получаем кадр и отображаем
    frame = picam2.capture_array()
    label = f"λ = OFF" if selected_wl is None else f"λ = {selected_wl} nm"
    cv2.putText(frame, label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Exposure = {exp} us, Gain = {gain:.1f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imshow("Camera", frame)

    key = cv2.waitKey(1)
    if key == 27:  # ESC
        break

# === Завершение ===
for led in LED_PINS.values():
    led.off()
picam2.close()
cv2.destroyAllWindows()
