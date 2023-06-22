__all__ = ['SagaStateRepository']

import datetime

from .status import SagaStatus
from ..saga.stateful import AbstractSagaStateRepository
from ..steps import BaseStep


class SagaStateRepository(AbstractSagaStateRepository):
    def __init__(self, saga, state):
        self.saga = saga
        self.state = state

    def get_saga_state_filter(self, saga_state_id: int) -> object:
        return self.state.objects.filter(pk=saga_state_id)

    def get_saga_state_by_id(self, saga_state_id: int) -> object:
        return self.get_saga_state_filter(saga_state_id).first()

    def update_status(self, saga_state_id: int, status: str) -> object:
        saga_state_filter = self.get_saga_state_filter(saga_state_id)

        # Update Saga record in saga table
        self.saga.objects.filter(pk=saga_state_filter.first().saga.id).update(status=_get_saga_status(status))
        return saga_state_filter.update(status=status)

    def update(self, saga_state_id: int, **fields_to_update: str) -> object:
        return self.get_saga_state_filter(saga_state_id).update(**fields_to_update)

    def on_step_failure(self, saga_state_id: int, failed_step: BaseStep, initial_failure_payload: dict) -> object:
        return self.get_saga_state_filter(saga_state_id).update(failed_step=failed_step.name,
                                                                failed_at=datetime.datetime.utcnow(),
                                                                failure_details=initial_failure_payload
                                                                )

    def get_saga_payload(self, saga_state: object) -> dict:
        return saga_state.saga.payload


def _get_saga_status(status):
    status_ = status.split('.')[-1]
    map_ = {'running': SagaStatus.PENDING.value,
            'succeeded': SagaStatus.APPROVED.value,
            'failed': SagaStatus.REJECTED.value,
            'approved': SagaStatus.APPROVED.value
            }
    return map_.get(status_, SagaStatus.REJECTED.value)
