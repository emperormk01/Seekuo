"""Engine registry."""

from .base import Engine, RequestSpec, Result
from .brave import Brave
from .ddg_lite import DuckDuckGoLite

ALL_ENGINES: dict[str, Engine] = {
    "brave": Brave(),
    "ddg-lite": DuckDuckGoLite(),
    "duckduckgo": DuckDuckGoLite(),
}

__all__ = ["Engine", "RequestSpec", "Result", "ALL_ENGINES"]
