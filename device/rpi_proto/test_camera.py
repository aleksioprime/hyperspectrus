from picamera2 import Picamera2
import time

def take_photo(filename="photo.jpg"):
    picam2 = Picamera2()

    # Настройка камеры (можно оставить автоматической)
    config = picam2.create_still_configuration()
    picam2.configure(config)

    # Запуск камеры
    picam2.start()

    # Небольшая задержка для автофокуса/автонастроек
    time.sleep(2)

    # Сделать фото
    picam2.capture_file(filename)
    print(f"Фото сохранено: {filename}")

    # Остановить камеру
    picam2.close()

if __name__ == "__main__":
    take_photo("test_picamera2.jpg")
