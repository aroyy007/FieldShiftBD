from __future__ import annotations

from collections.abc import Callable
from types import TracebackType

from sqlalchemy.orm import Session


class SQLAlchemyUnitOfWork:
    """One explicit transaction shared by the coordinator and owner operations."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self.session: Session | None = None
        self._transaction = None

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self.session = self._session_factory()
        if self.session.in_transaction():
            self.session.close()
            self.session = None
            raise RuntimeError("unit of work requires a fresh session without an open transaction")
        self._transaction = self.session.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        assert self.session is not None and self._transaction is not None
        try:
            if exc_type is None:
                self._transaction.commit()
            else:
                self._transaction.rollback()
        finally:
            self.session.close()
        return False


class SQLAlchemyUnitOfWorkFactory:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __call__(self) -> SQLAlchemyUnitOfWork:
        return SQLAlchemyUnitOfWork(self._session_factory)
