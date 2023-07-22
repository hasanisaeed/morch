__all__ = ['AbstractSagaStateRepository', 'StatefulSaga']

import abc

from celery import Celery, Task

from ..helpers import success_task_name, failure_task_name
from .asynch import AsyncSaga
from ..steps import BaseStep, AsyncStep


class AbstractSagaStateRepository(abc.ABC):
    @abc.abstractmethod
    def get_saga_state_filter(self, saga_id: int) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def get_saga_state_by_id(self, saga_id: int) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def update_status(self, saga_id: int, status: str) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, saga_id: int, **fields_to_update: dict) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, fields_to_create: dict) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def on_step_failure(self, saga_id: int, failed_step: BaseStep, initial_failure_payload: dict) -> object:
        pass

    @abc.abstractmethod
    def get_saga_payload(self, saga_state: object) -> dict:
        pass

    @abc.abstractmethod
    def get_last_saga_state_payload(self, saga_id: int) -> dict:
        pass


class StatefulSaga(AsyncSaga, abc.ABC):
    """
    Note this class assumes sqlalchemy-mixins library is used.
    Use it rather as an example
    """
    saga_state_repository: AbstractSagaStateRepository = None

    def __init__(self, saga_state_id,
                 saga_state_repository: AbstractSagaStateRepository,
                 celery_app: Celery):

        self.saga_state_id = saga_state_id

        self.saga_state_repository = saga_state_repository
        if saga_state_id:
            self.saga_state = self.saga_state_repository.get_saga_state_by_id(saga_state_id)
        super().__init__(celery_app, saga_state_id)

    def run_step(self, step: BaseStep):
        self.saga_state_repository.update_status(self.saga_state_id, status=f'{step.name}.running')
        super().run_step(step)

    def compensate_step(self, step: BaseStep, initial_failure_payload: dict):
        self.saga_state_repository.update_status(self.saga_state_id, status=f'{step.name}.compensating')
        super().compensate_step(step, initial_failure_payload)
        self.saga_state_repository.update_status(self.saga_state_id, status=f'{step.name}.compensated')

    def on_step_success(self, step: AsyncStep, *args, **kwargs):
        self.saga_state_repository.update_status(self.saga_state_id, status=f'{step.name}.succeeded')
        super().on_async_step_success(step, *args, **kwargs)

    def on_step_failure(self, failed_step: AsyncStep, payload: dict):
        self.saga_state_repository.update_status(self.saga_state_id, status=f'{failed_step.name}.failed')
        super().on_async_step_failure(failed_step, payload)

    def on_saga_success(self):
        super().on_saga_success()
        self.saga_state_repository.update_status(self.saga_state_id, 'succeeded')

    def on_saga_failure(self, *args, **kwargs):
        super().on_saga_failure(*args, **kwargs)
        self.saga_state_repository.update_status(self.saga_state_id, 'failed')

    def compensate(self, failed_step: BaseStep,
                   initial_failure_payload: dict = None):
        self.saga_state_repository.on_step_failure(self.saga_state_id, failed_step, initial_failure_payload)
        super().compensate(failed_step, initial_failure_payload)

    @classmethod
    def register_async_step_handlers(cls,
                                     saga_state_repository: AbstractSagaStateRepository,
                                     celery_app: Celery):
        # noinspection PyTypeChecker
        dummy_saga_instance = cls(None, None, None)

        for step in dummy_saga_instance.async_steps:
            cls.register_success_handler_for_step(saga_state_repository,
                                                  celery_app, step)
            cls.register_failure_handler_for_step(saga_state_repository,
                                                  celery_app, step)

    @classmethod
    def register_success_handler_for_step(cls,
                                          saga_state_repository: AbstractSagaStateRepository,
                                          celery_app: Celery, step: AsyncStep):
        def on_success_handler(celery_task: Task, saga_id: int, payload: dict):
            saga = cls(saga_id,
                       saga_state_repository=saga_state_repository,
                       celery_app=celery_app)

            step_ = saga.get_async_step_by_success_task_name(celery_task.name)
            saga.on_async_step_success(step_, payload)

        # celery_app.conf.q
        celery_app.task(name=success_task_name(step.base_task_name),
                        bind=True)(on_success_handler)

    @classmethod
    def register_failure_handler_for_step(cls, saga_state_repository: AbstractSagaStateRepository,
                                          celery_app: Celery,
                                          step: AsyncStep):
        def on_failure_handler(celery_task: Task, saga_id: int, payload: dict):
            saga = cls(saga_id,
                       saga_state_repository=saga_state_repository,
                       celery_app=celery_app)
            step_ = saga.get_async_step_by_failure_task_name(celery_task.name)
            saga.on_async_step_failure(step_, payload)

        celery_app.task(name=failure_task_name(step.base_task_name),
                        bind=True)(on_failure_handler)
