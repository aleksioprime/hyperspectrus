import os

LOG_DIR = os.path.join(os.path.expanduser("~"), ".hyperspectrus_logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "short": {
            "format": "[%(levelname)s] %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "short",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
    "loggers": {
        # Если нужны отдельные настройки для модулей — добавьте здесь
        # "my_module": {
        #     "handlers": ["file"],
        #     "level": "DEBUG",
        #     "propagate": False,
        # },
    },
}
