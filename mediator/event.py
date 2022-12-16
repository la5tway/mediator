from typing import Any, Generic, TypeVar

from .base import Handler, Request


class Event(Request):
    ...


TEvent = TypeVar("TEvent", bound=Event)


class EventHandler(Handler, Generic[TEvent]):
    async def execute(
        self,
        *,
        event: TEvent,
        **kwargs: Any,
    ) -> None:
        ...
