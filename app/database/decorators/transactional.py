import functools
import inspect
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..transaction import Transaction, in_transaction

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def transactional(
    func: Callable[P, Awaitable[T]],
) -> Callable[P, Awaitable[T]]:
    """
    Decorator for executing a function within a transaction.

    If the function execution succeeds, the transaction is committed (if outermost).
    If an exception is raised, the transaction is rolled back (if outermost).

    The function being decorated must have a session parameter or be a method
    of a class with a self.session attribute.

    Usage:
        @transactional
        async def my_function(session: AsyncSession, ...):
            -- Function code here --

        <br>
        OR <br>

        class MyService:
            def __init__(self, session: AsyncSession):
                self.session = session

            @transactional
            async def my_method(self, ...):
                -- Method code here --
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:  # type: ignore
        session = None

        if args and hasattr(args[0], "session"):
            session = args[0].session  # type: ignore
        elif "session" in kwargs:
            session = kwargs["session"]  # type: ignore
        else:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            try:
                session_idx = param_names.index("session")
                if len(args) > session_idx:
                    session = args[session_idx]  # type: ignore
                else:
                    raise ValueError("Session argument is required but not provided")
            except ValueError:
                raise ValueError("Could not find session parameter in function or method")

        if not isinstance(session, AsyncSession):
            raise TypeError("Session must be an instance of `AsyncSession` ")

        # Execute the function either within the current transaction or in a new one.
        if in_transaction():
            return await func(*args, **kwargs)

        async with Transaction(session):
            return await func(*args, **kwargs)

    return wrapper
