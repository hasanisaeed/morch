__all__ = ['saga_step_handler',
           'no_response_saga_step_handler',
           'send_saga_response']

import functools
import logging
from dataclasses import asdict

from typing import Union
import celery
from celery import Celery, Task

from . import success_task_name, serialize_saga_error, failure_task_name

logger = logging.getLogger(__name__)


def send_saga_response(celery_app: Celery,
                       response_task_name: str,
                       response_queue_name: str,
                       saga_id: int,
                       payload):  # assuming payload is a @dataclass
    return celery_app.send_task(response_task_name,
                                args=[saga_id, payload],
                                queue=response_queue_name)


def _saga_step_handler(response_queue: Union[str, None]):
    def inner(func):
        @functools.wraps(func)
        def wrapper(celery_task: Task, saga_id: int, payload: dict):
            try:
                response_payload = func(celery_task, saga_id, payload)  # type: Union[dict, None]
                # use convention response task name
                task_name = success_task_name(celery_task.name)
            except BaseException as exc:
                # let Celery handle retries
                if isinstance(exc, celery.exceptions.Retry):
                    raise

                logger.exception(exc)

                # serialize error in a unified way
                response_payload = asdict(serialize_saga_error(exc))
                # use convention response task name
                task_name = failure_task_name(celery_task.name)

            if response_queue:
                send_saga_response(celery_task.app,
                                   task_name,
                                   response_queue,
                                   saga_id,
                                   response_payload)

        return wrapper

    return inner


def saga_step_handler(response_queue: str):
    return _saga_step_handler(response_queue)


no_response_saga_step_handler = _saga_step_handler(response_queue=None)
