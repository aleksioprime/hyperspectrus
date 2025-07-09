import logging
import time

from src.models.patient import Session
from src.db.postgres import SyncSessionLocal
from src.constants.celery import CeleryStatus
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


def update_session_fields(session_id, **fields):
    with SyncSessionLocal() as db:
        obj = db.query(Session).filter(Session.id == session_id).first()
        if obj:
            for key, value in fields.items():
                setattr(obj, key, value)
            db.commit()
            logger.info(f"Обновлены поля {fields} в сеансе {session_id}")
        else:
            logger.warning(f"Сеанс {session_id} не найден для обновления {fields}")


@celery_app.task(bind=True)
def process_session(self, session_id: str):
    update_session_fields(session_id, processing_status=CeleryStatus.STARTED)

    try:
        logger.info(f"Начало обработки данных сеанса {session_id}")
        time.sleep(5)
        logger.info(f"Обработка сеанса {session_id} завершена")
        update_session_fields(
            session_id,
            processing_status=CeleryStatus.SUCCESS,
            processing_task_id=None
        )
    except Exception:
        update_session_fields(
            session_id,
            processing_status=CeleryStatus.FAILURE,
            processing_task_id=None
        )
        raise

    return {"status": "finished", "session_id": session_id}
