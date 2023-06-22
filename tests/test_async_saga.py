from typing import Dict
from unittest.mock import MagicMock

from morch import AsyncSaga, SyncStep, AsyncStep


def test_run_success_many_step():
    start_step_compensation_mock = MagicMock()

    step_2_success_mock = MagicMock()
    step_2_failure_mock = MagicMock()

    step_3_success_mock = MagicMock()
    step_3_failure_mock = MagicMock()

    step_4_success_mock = MagicMock()
    step_4_failure_mock = MagicMock()

    fake_action_mock = MagicMock()

    last_action_mock = MagicMock()

    on_success_mock = MagicMock()
    on_failure_mock = MagicMock()

    class Saga(AsyncSaga):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.steps = [
                SyncStep(name='start_step', compensation=start_step_compensation_mock),
                AsyncStep(name='step2',
                          action=fake_action_mock,
                          queue='queue2',
                          base_task_name='task2',
                          on_success=step_2_success_mock,
                          on_failure=step_2_failure_mock),
                AsyncStep(name='step3',
                          action=fake_action_mock,
                          queue='queue3',
                          base_task_name='task3',
                          on_success=step_3_success_mock,
                          on_failure=step_3_failure_mock),
                AsyncStep(name='step4',
                          action=fake_action_mock,
                          queue='queue4',
                          base_task_name='task4',
                          on_success=step_4_success_mock,
                          on_failure=step_4_failure_mock),

                SyncStep(name='last_step', action=last_action_mock),
            ]

        on_saga_success = on_success_mock
        on_saga_failure = on_failure_mock

    celery_app = FakeCeleryApp()
    Saga.register_async_step_handlers(celery_app)

    fake_saga_id = 1
    Saga(celery_app, saga_id=fake_saga_id).execute()

    fake_action_mock.assert_called_once()

    celery_task_params = dict(saga_id=fake_saga_id, payload={'message': 'Ok'})

    celery_app.launch_celery_task('task2.response.success', **celery_task_params)
    step_2_success_mock.assert_called_once()

    celery_app.launch_celery_task('task3.response.success', **celery_task_params)
    step_3_success_mock.assert_called_once()

    celery_app.launch_celery_task('task4.response.success', **celery_task_params)
    step_4_success_mock.assert_called_once()

    # finally
    on_success_mock.assert_called_once()

    start_step_compensation_mock.assert_not_called()


def test_run_failure_many_step():
    start_step_compensation_mock = MagicMock()

    step_2_success_mock = MagicMock()
    step_2_failure_mock = MagicMock()
    step_2_compensation_mock = MagicMock()

    step_3_success_mock = MagicMock()
    step_3_failure_mock = MagicMock()
    step_3_compensation_mock = MagicMock()

    step_4_success_mock = MagicMock(side_effect=Exception())
    step_4_failure_mock = MagicMock()

    fake_action_mock = MagicMock()

    last_action_mock = MagicMock()

    on_success_mock = MagicMock()
    on_failure_mock = MagicMock()

    class Saga(AsyncSaga):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.steps = [
                SyncStep(name='start_step', compensation=start_step_compensation_mock),
                AsyncStep(name='step2',
                          action=fake_action_mock,
                          queue='queue2',
                          base_task_name='task2',
                          compensation=step_2_compensation_mock,
                          on_success=step_2_success_mock,
                          on_failure=step_2_failure_mock),
                AsyncStep(name='step3',
                          action=fake_action_mock,
                          queue='queue3',
                          base_task_name='task3',
                          compensation=step_3_compensation_mock,
                          on_success=step_3_success_mock,
                          on_failure=step_3_failure_mock),
                AsyncStep(name='step4',
                          action=fake_action_mock,
                          queue='queue4',
                          base_task_name='task4',
                          on_success=step_4_success_mock,
                          on_failure=step_4_failure_mock),

                SyncStep(name='last_step', action=last_action_mock),
            ]

        on_saga_success = on_success_mock
        on_saga_failure = on_failure_mock

    celery_app = FakeCeleryApp()
    Saga.register_async_step_handlers(celery_app)

    fake_saga_id = 1
    Saga(celery_app, saga_id=fake_saga_id).execute()

    fake_action_mock.assert_called_once()

    celery_task_params = dict(saga_id=fake_saga_id, payload={'message': 'Ok'})

    celery_app.launch_celery_task('task2.response.success', **celery_task_params)
    step_2_success_mock.assert_called_once()

    celery_app.launch_celery_task('task3.response.success', **celery_task_params)
    step_3_success_mock.assert_called_once()

    celery_app.launch_celery_task('task4.response.failure', **celery_task_params)
    step_4_failure_mock.assert_called_once()

    step_2_compensation_mock.assert_called_once()
    step_3_compensation_mock.assert_called_once()
    start_step_compensation_mock.assert_called_once()

    # finally
    on_failure_mock.assert_called_once()


# ===========================
class FakeCeleryApp:
    send_task = MagicMock()
    _tasks_handlers: Dict[str, callable]

    def __init__(self):
        self._task_handlers = {}

    def task(self, name: str, bind: bool = True, *args, **kwargs) -> callable:
        def wrapper(task_handler: callable):
            self._task_handlers[name] = FakeCeleryTask(self, name, task_handler, bind)

        return wrapper

    def launch_celery_task(self, name: str, *args, **kwargs):
        if self._task_handlers.get(name) is None:
            raise KeyError(f">> Celery task <{name}> is not defined!")
        self._task_handlers[name](*args, **kwargs)


class FakeCeleryTask:
    def __init__(self, app: FakeCeleryApp, name: str, task_handler: callable, bind: bool = False):
        self.app = app
        self.name = name
        self.bind = bind
        self.task_handler = task_handler

    def __call__(self, *args, **kwargs):
        task_handler = self.task_handler
        if self.bind:
            task_handler(self, *args, **kwargs)
        else:
            task_handler(*args, **kwargs)
