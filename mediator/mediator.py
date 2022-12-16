import logging
from collections import defaultdict
from contextlib import AsyncExitStack
from functools import wraps
from inspect import isawaitable, isclass
from typing import Any, Callable

from .base import HandlerFunction
from .command import Command, CommandHandler, TCommandResult
from .common import Provider
from .event import EventHandler
from .exc import CommandHandlerNotFoundError, EventHandlerNotFoundError


class Mediator:
    def __init__(
        self,
        provider: Provider,
        exit_stack_factory: Callable[[], AsyncExitStack],
        logger: logging.Logger | None = None,
    ) -> None:
        self._commands: dict[type[Command[Any]], HandlerFunction] = {}
        self._events: dict[type, list[HandlerFunction]] = defaultdict(list)
        self._provider = provider
        self._exit_stack_factory = exit_stack_factory
        if not logger:
            self._logger = logging.getLogger(self.__class__.__name__)
        else:
            self._logger = logger.getChild(self.__class__.__name__)

    def bind_command(
        self,
        command_type: type[Command[Any]],
        handler_type: type[CommandHandler[Any, Any]] | CommandHandler[Any, Any],
    ):
        if isclass(handler_type):
            handler = handler_type(
                **self._provider.resolve_params(
                    method=handler_type,
                )
            )
            execute = self._wrap(handler, {"command"})
        else:
            execute = self._wrap(handler_type, {"command"})
        self._commands[command_type] = execute

    def bind_event(
        self,
        event_type: type,
        handler_type: type[EventHandler[Any]] | HandlerFunction,
    ):
        if isclass(handler_type):
            handler = handler_type(
                **self._provider.resolve_params(
                    method=handler_type,
                )
            )
            execute = self._wrap(handler, {"event"})
        else:
            execute = self._wrap(handler_type, {"event"})
        self._events[event_type].append(execute)

    async def execute(
        self,
        command: Command[TCommandResult],
    ) -> TCommandResult:
        try:
            async with self._exit_stack_factory():
                return await self._commands[type(command)](command=command)
        except LookupError:
            raise CommandHandlerNotFoundError(
                f"Command handler not found for {type(command)}"
            )

    async def publish(self, event: Any):
        total = 0
        event_type = type(event)
        subscribers = self._events.get(event_type)
        if subscribers:
            for subscriber in subscribers:
                await subscriber(event=event)
                total += 1
        for parent in event_type.__mro__:
            if parent is event_type:
                continue
            subscribers = self._events.get(parent)
            if subscribers:
                for subscriber in subscribers:
                    await subscriber(event=event)
                    total += 1
        if not total:
            raise EventHandlerNotFoundError(
                f"Event handler not found for {event_type}",
            )

    async def publish_all(self, *event: Any):
        for e in event:
            await self.publish(e)

    def _wrap(
        self,
        func: Callable[..., Any],
        exclude_names: set[str] | None = None,
    ):
        params = self._provider.get_params(func, exclude_names)

        @wraps(func)
        async def resolve_wrapper(**kwargs: Any):
            resolved = self._provider.resolve_signature(
                params,
                **kwargs,
            )
            for k, v in resolved.items():
                if isawaitable(v):
                    resolved[k] = await v

            return await func(**kwargs, **resolved)

        return resolve_wrapper
