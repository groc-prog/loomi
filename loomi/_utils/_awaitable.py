from inspect import isawaitable
from typing import Awaitable, Generic, TypeVar, Union

T = TypeVar("T")


class _AwaitableResult(Generic[T]):
    __func: Union[T, Awaitable[T]]

    def __init__(self, func: Union[T, Awaitable[T]]):
        self.__func = func

    def __await__(self):
        async def resolve_async() -> T:
            if isawaitable(self.__func):
                return await self.__func
            return self.__func

        return resolve_async().__await__()

    def sync(self) -> T:
        """
        Runs the provided function in a sync way.

        Raises:
            RuntimeError: If the function is async.

        Returns:
            T: The result of the function.
        """
        if isawaitable(self.__func):
            raise RuntimeError("`.sync()` should not be called on a coroutine")
        return self.__func
