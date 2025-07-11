from PyQt5.QtCore import QObject, pyqtSignal
import threading
import time
import logging

logger = logging.getLogger(__name__)

class ShootWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    button_wait = pyqtSignal(int)  # сигнал: жду нажатия кнопки для кадра с индексом idx

    def __init__(self, spectra, camera_widget, led_controller, save_func, task_id, test_mode=False, by_button=False):
        super().__init__()
        self.spectra = spectra
        self.camera_widget = camera_widget
        self.led_controller = led_controller
        self.save_func = save_func
        self.task_id = task_id
        self.test_mode = test_mode
        self.by_button = by_button
        self._button_event = threading.Event() if by_button else None

    def run(self):
        logger.info(f"Запуск воркера съёмки: task_id={self.task_id}, test_mode={self.test_mode}, by_button={self.by_button}")
        try:
            start_time = time.time()

            frames = []
            for idx, spec in enumerate(self.spectra):
                status = f"Снимок {idx + 1} из {len(self.spectra)} (λ = {spec} нм)"
                logger.info(f"[{self.task_id}] {status}, спектр: {spec}")
                self.progress.emit(status)
                # Включить LED по длине волны
                self.led_controller.on(spec)
                logger.info(f"Включён светодиод для спектра {spec}")

                if self.by_button:
                    logger.info(f"Ожидание нажатия кнопки для кадра {idx+1}")
                    self.button_wait.emit(idx)
                    self._button_event.wait()
                    self._button_event.clear()
                    logger.info(f"Кнопка нажата для кадра {idx+1}")
                # else:
                    # time.sleep(0.5)

                # Снимаем кадр
                frame = self.camera_widget.get_frame(spec)
                frames.append(frame)
                logger.info(f"Кадр получен")
                # time.sleep(0.5)

                # Выключить LED по длине волны
                self.led_controller.off(spec)
                logger.info(f"Светодиод для спектра {spec} выключен")

            # Сохраняем снимок, где spec — длина волны (spectrum_id)
            for frame, spec in zip(frames, self.spectra):
                self.save_func(self.task_id, frame, spec)
                logger.info(f"[{self.task_id}] Снимок спектра {spec} сохранён")
            else:
                logger.warning(f"[{self.task_id}] Не удалось получить кадр для спектра: {spec}")

            logger.info(f"Съёмка завершена для task_id={self.task_id}")
            elapsed = time.time() - start_time  # конец таймера
            logger.info(f"Время съёмки всей серии: {elapsed:.2f} сек")

            self.camera_widget.picam2.set_controls({
                "AeEnable": True
            })

            self.finished.emit()
        except Exception as e:
            logger.exception(f"Ошибка в процессе съёмки task_id={self.task_id}: {e}")
            self.error.emit(str(e))

    # Метод для вызова из основного потока после нажатия кнопки
    def button_pressed(self):
        if self._button_event:
            self._button_event.set()
