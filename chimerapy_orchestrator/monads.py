from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


class Result(ABC, Generic[T, E]):
    """A result type that can be either Ok or Err."""

    def __init__(self, value: Any):
        self._value = value

    @abstractmethod
    def map(self, func: Callable) -> "Result":
        return NotImplemented

    @abstractmethod
    def map_error(self, Callable) -> "Result":
        return NotImplemented

    @abstractmethod
    def unwrap(self) -> Union[T, E]:
        return NotImplemented

    @abstractmethod
    def ok(self) -> "MayBe[T, E]":
        return NotImplemented


class MayBe(ABC, Generic[T, E]):
    """A type that can be either Some or None."""

    @abstractmethod
    def is_some(self) -> bool:
        return NotImplemented

    @abstractmethod
    def is_none(self) -> bool:
        return NotImplemented

    @abstractmethod
    def unwrap(self) -> T:
        return NotImplemented

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        return NotImplemented

    @abstractmethod
    def unwrap_or_else(self, func: Callable) -> T:
        return NotImplemented

    @abstractmethod
    def ok_or(self, err: Any) -> Result[T, E]:
        return NotImplemented

    @abstractmethod
    def ok_or_else(self, func: Callable) -> Result[T, E]:
        return NotImplemented

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> "MayBe[U, E]":
        return NotImplemented

    @abstractmethod
    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        return NotImplemented

    @abstractmethod
    def map_or_else(self, default: Callable, func: Callable[[T], U]) -> U:
        return NotImplemented


class some(MayBe):
    """Represents a Some value."""

    def __init__(self, value: T):
        self._value = value

    def is_some(self) -> bool:
        return True

    def is_none(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, func: Callable) -> T:
        return self._value

    def ok_or(self, err: Any) -> Result[T, E]:
        return Ok(self._value)

    def ok_or_else(self, func: Callable) -> Result[T, E]:
        return Ok(self._value)

    def map(self, func: Callable[[T], U]) -> "MayBe[U, E]":
        return some(func(self._value))

    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        return func(self._value)

    def map_or_else(self, default: Callable, func: Callable[[T], U]) -> U:
        return func(self._value)


class none(MayBe):
    """Represents a None value."""

    def is_some(self) -> bool:
        return False

    def is_none(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise Exception("Cannot unwrap a None value")

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, func: Callable) -> T:
        return func()

    def ok_or(self, err: Any) -> Result[T, E]:
        return Err(err)

    def ok_or_else(self, func: Callable) -> Result[T, E]:
        return Err(func())

    def map(self, func: Callable[[T], U]) -> "MayBe[U, E]":
        return none()

    def map_or(self, default: U, func: Callable[[T], U]) -> U:
        return default

    def map_or_else(self, default: Callable, func: Callable[[T], U]) -> U:
        return default()


class Ok(Result[T, E]):
    """Ok is a Result that contains a success value."""

    def __init__(self, value: T):
        super().__init__(value)

    def map(self, func: Callable) -> "Result":
        try:
            return Ok(func(self._value))
        except Exception as e:
            return Err(e)

    def map_error(self, func: Callable) -> "Result":
        return Ok(self._value)

    def unwrap(self) -> T:
        return self._value

    def ok(self) -> "MayBe[T, E]":
        return some(self._value)


class Err(Result[T, E]):
    """Err is a Result that contains an error value."""

    def __init__(self, value: E):
        super().__init__(value)

    def map(self, func: Callable) -> "Result":
        return Err(self._value)

    def map_error(self, func: Callable) -> "Result":
        try:
            return Err(func(self._value))
        except Exception as e:
            return Err(e)

    def unwrap(self) -> E:
        if isinstance(self._value, Exception):
            raise self._value
        else:
            return self._value

    def ok(self) -> "MayBe[T, E]":
        return none()
