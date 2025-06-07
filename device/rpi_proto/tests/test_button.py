from gpiozero import Button
from signal import pause

button = Button("GPIO20", pull_up=True)

def on_press():
    print("Нажата кнопка на GPIO20!")

def on_release():
    print("Кнопка отпущена.")

button.when_pressed = on_press
button.when_released = on_release

print("Жду нажатия кнопки на GPIO20...")
pause()  # Ожидание событий, чтобы программа не завершалась
