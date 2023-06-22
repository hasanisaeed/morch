__all__ = ['BaseStep']

from typing import Callable
from abc import ABC

from ..helpers import do_nothing


class BaseStep(ABC):
    def __init__(self, name: str,
                 action: Callable = do_nothing,
                 compensation: Callable = do_nothing):
        self.name = name
        self.action = action
        self.compensation = compensation
