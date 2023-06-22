__all__ = ['SagaStatus']

import enum


class SagaStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
