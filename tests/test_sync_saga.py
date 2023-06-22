from unittest.mock import MagicMock

from morch import SyncStep, BaseSaga


def test_run_success():
    start_step_action_mock = MagicMock()
    start_step_compensation_mock = MagicMock()

    fake_action_mock = MagicMock()

    last_step_compensation_mock = MagicMock()

    on_success_mock = MagicMock()
    on_failure_mock = MagicMock()

    class SyncSaga(BaseSaga):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.steps = [
                SyncStep(name='start_step', action=start_step_action_mock, compensation=start_step_compensation_mock, ),
                SyncStep(name='second_step', action=fake_action_mock),
                SyncStep(name='last_step', compensation=last_step_compensation_mock, action=fake_action_mock),
            ]

        on_saga_success = on_success_mock
        on_saga_failure = on_failure_mock

    SyncSaga(saga_id=1).execute()
    on_success_mock.assert_called_once()
    on_failure_mock.assert_not_called()


def test_run_failure():
    start_step_action_mock = MagicMock()
    start_step_compensation_mock = MagicMock()

    fake_action_mock = MagicMock(side_effect=Exception('some exception'))

    last_step_compensation_mock = MagicMock()

    on_success_mock = MagicMock()
    on_failure_mock = MagicMock()

    class SyncSaga(BaseSaga):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.steps = [
                SyncStep(name='start_step', action=start_step_action_mock, compensation=start_step_compensation_mock, ),
                SyncStep(name='second_step', action=fake_action_mock),
                SyncStep(name='last_step', compensation=last_step_compensation_mock, action=fake_action_mock),
            ]

        on_saga_success = on_success_mock
        on_saga_failure = on_failure_mock

    SyncSaga(saga_id=1).execute()

    on_success_mock.assert_not_called()
    on_failure_mock.assert_called_once()
    start_step_compensation_mock.assert_called_once()
    last_step_compensation_mock.assert_not_called()
