__all__ = ['auto_retry_then_reraise']

import functools

from celery import Task
from celery.exceptions import MaxRetriesExceededError


def auto_retry_then_reraise(max_retries: int = 3, **retry_kwargs):
    def inner(func):

        @functools.wraps(func)
        def wrapper(self: Task, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                try:
                    raise self.retry(exc=exc, max_retries=max_retries, **retry_kwargs)
                except MaxRetriesExceededError:
                    raise exc

        return wrapper

    return inner
