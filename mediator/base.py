from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .mediator import Mediator


@dataclass(slots=True)
class Request:
    ...


class Handler:
    def __init__(self, mediator: "Mediator") -> None:
        self.mediator = mediator

    async def __call__(self, **kwargs: Any) -> Any:
        ...


HandlerFunction = Callable[..., Any]
