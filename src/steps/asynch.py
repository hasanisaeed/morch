__all__ = ['AsyncStep']

from typing import Callable

from src.helpers.utils import do_nothing
from src.steps import BaseStep


class AsyncStep(BaseStep):
    def __init__(self, base_task_name: str,
                 queue: str,
                 on_success: Callable = do_nothing,
                 on_failure: Callable = do_nothing,
                 *args,
                 **kwargs):
        self.base_task_name = base_task_name
        self.queue = queue
        self.on_success = on_success
        self.on_failure = on_failure

        super().__init__(*args, **kwargs)
