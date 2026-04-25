__all__ = ["MessagingError", "SagaFailed", "SagaRolledBack"]


class MessagingError(Exception):
    code = "messaging_error"


class SagaFailed(MessagingError):
    code = "saga_failed_error"


class SagaRolledBack(MessagingError):
    code = "saga_rolled_back_error"
