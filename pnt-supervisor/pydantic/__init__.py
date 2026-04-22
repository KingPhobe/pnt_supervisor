"""Minimal local subset of the pydantic API used for offline testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConfigDict(dict):
    """Compatibility shim for pydantic.ConfigDict."""


@dataclass(slots=True)
class _FieldInfo:
    default: Any = ...
    default_factory: Any | None = None


def Field(default: Any = ..., *, default_factory: Any | None = None) -> Any:
    return _FieldInfo(default=default, default_factory=default_factory)


class BaseModel:
    """Small BaseModel-compatible initializer for declared fields."""

    def __init__(self, **kwargs: Any) -> None:
        annotations = getattr(self.__class__, "__annotations__", {})
        for name in annotations:
            if name in kwargs:
                value = kwargs[name]
            else:
                class_value = getattr(self.__class__, name, ...)
                if isinstance(class_value, _FieldInfo):
                    if class_value.default_factory is not None:
                        value = class_value.default_factory()
                    elif class_value.default is not ...:
                        value = class_value.default
                    else:
                        raise TypeError(f"Missing required field: {name}")
                elif class_value is not ...:
                    value = class_value
                else:
                    raise TypeError(f"Missing required field: {name}")
            setattr(self, name, value)
