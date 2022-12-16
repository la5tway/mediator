from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .base import Handler, Request


class CommandResult:
    ...


TCommandResult = TypeVar(
    "TCommandResult",
    bound=CommandResult | None,
)


@dataclass(slots=True)
class Command(Request, Generic[TCommandResult]):
    ...


TCommand = TypeVar("TCommand", bound=Command[Any])


class CommandHandler(Handler, Generic[TCommand, TCommandResult]):
    async def __call__(
        self,
        *,
        command: TCommand,
        **kwargs: Any,
    ) -> TCommandResult | None:
        ...
