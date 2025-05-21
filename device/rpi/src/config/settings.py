import os

"""
Глобальные настройки проекта: директории для фотографий и иконок.
"""

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PHOTO_DIR = os.path.join(BASE_DIR, 'photos')

# Гарантируем, что директория для фото существует
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

ICON_DIR = os.path.join(BASE_DIR, 'assets', 'icons')

def icon_path(name):
    """
    Возвращает путь к иконке с именем name. Цвет иконок: #018073
    """
    return os.path.join(ICON_DIR, name)
