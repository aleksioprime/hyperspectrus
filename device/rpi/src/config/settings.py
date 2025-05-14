import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PHOTO_DIR = os.path.join(BASE_DIR, 'photos')
PHOTO_SERIES_COUNT = 5


if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

ICON_DIR = os.path.join(BASE_DIR, 'assets', 'icons')
def icon_path(name):
    return os.path.join(ICON_DIR, name)

SPECTRA = [
    (255, 0, 0),     # Красный
    (0, 255, 0),     # Зелёный
    (0, 0, 255),     # Синий
    (255, 255, 0),   # Жёлтый
    (255, 255, 255), # Белый
]

##018073