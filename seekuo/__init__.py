"""Seekuo: agent-friendly web search toolbox. No API keys."""

from .agent import agent_search
from .client import fetch, random_impersonate
from .engines import ALL_ENGINES

__version__ = "0.1.0"
__all__ = ["agent_search", "fetch", "random_impersonate", "ALL_ENGINES"]
