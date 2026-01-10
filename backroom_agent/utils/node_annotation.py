from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, TypeVar

NodeKind = Literal["llm", "normal"]


@dataclass(frozen=True, slots=True)
class NodeAnnotation:
    kind: NodeKind


_ANNOTATION_ATTR = "__backroom_node_annotation__"

F = TypeVar("F", bound=Callable[..., Any])


def annotate_node(kind: NodeKind) -> Callable[[F], F]:
    """Attach lightweight metadata to a node callable.

    We keep this as a simple runtime attribute so it works with LangGraph callables
    (sync/async) without requiring wrapper functions.
    """

    def decorator(fn: F) -> F:
        setattr(fn, _ANNOTATION_ATTR, NodeAnnotation(kind=kind))
        return fn

    return decorator


def get_node_annotation(fn: Callable[..., Any]) -> Optional[NodeAnnotation]:
    value = getattr(fn, _ANNOTATION_ATTR, None)
    if isinstance(value, NodeAnnotation):
        return value
    return None


def is_llm_node(fn: Callable[..., Any]) -> bool:
    ann = get_node_annotation(fn)
    return bool(ann and ann.kind == "llm")
