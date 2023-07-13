import inspect
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, Field

from chimerapy.node import Node


class AttributeType(str, Enum):
    """The type of the parameter."""

    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    ARRAY = "ARRAY"
    TUPLE = "TUPLE"
    OBJECT = "OBJECT"
    ENUM = "ENUM"
    UNKNOWN = "UNKNOWN"


class NodeAttributeMeta(BaseModel):
    name: str = Field(..., description="The name of the parameter.")

    value: Any = Field(
        default=None, description="The default value of the parameter."
    )

    type: AttributeType = Field(
        default=None, description="The type of the parameter."
    )

    choices: List[Any] = Field(
        default=[], description="The choices of the parameter."
    )

    required: bool = Field(
        default=False, description="Whether the parameter is required."
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


class ParamMeta:
    empty = inspect.Parameter.empty

    def __init__(
        self,
        *,
        name: str,
        default: Any = inspect.Parameter.empty,
        annotation: Any = inspect.Parameter.empty,
    ) -> None:
        self.name = name
        self.default = default
        self.annotation = annotation


def get_params_from_function(func: Callable[..., Any]) -> Dict[str, ParamMeta]:
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    params = {}
    for param in signature.parameters.values():
        default = param.default
        annotation = param.annotation
        if param.name in type_hints:
            # Resolve forward references.
            annotation = type_hints[param.name]

        params[param.name] = ParamMeta(
            name=param.name, default=default, annotation=annotation
        )
    return params


def _is_a_type(annotation: Any, type_) -> bool:
    """Check if a type annotation is of type type_."""

    if annotation is type_:
        return True

    if get_origin(annotation) is type_:
        return True

    if get_origin(annotation) is Union:
        return any(_is_a_type(arg, type_) for arg in get_args(annotation))

    if type_ is Enum:
        return issubclass(annotation, Enum)

    return False


def _parse_param_type(annotation: Any) -> AttributeType:
    """Parse the type of a parameter."""
    if annotation is inspect.Parameter.empty:
        return AttributeType.UNKNOWN
    if _is_a_type(annotation, str):
        return AttributeType.STRING
    if _is_a_type(annotation, int):
        return AttributeType.INTEGER
    if _is_a_type(annotation, float):
        return AttributeType.FLOAT
    if _is_a_type(annotation, bool):
        return AttributeType.BOOLEAN
    if _is_a_type(annotation, list):
        return AttributeType.ARRAY
    if _is_a_type(annotation, tuple):
        return AttributeType.TUPLE
    if _is_a_type(annotation, dict):
        return AttributeType.OBJECT
    if _is_a_type(annotation, Enum):
        return AttributeType.ENUM

    return AttributeType.UNKNOWN


def _get_choices(annotation: Any) -> List[Any]:
    """Get the choices of a parameter."""

    if _is_a_type(annotation, Enum):
        return [choice.value for choice in annotation]

    if _is_a_type(annotation, bool):
        return [True, False]

    return []


def get_node_class_params(
    node_class: Type[Node],
) -> Dict[str, NodeAttributeMeta]:
    """Get the parameters of a node class's __init__ function."""
    params = {}

    assert issubclass(
        node_class, Node
    ), f"node_class must be a subclass of Node. Got {node_class}"

    for cls in reversed(node_class.__mro__):
        if cls in (Node, object):
            continue
        cls_params = get_params_from_function(cls.__init__)
        cls_params.pop("self", None)
        cls_params.pop("kwargs", None)
        cls_params.pop("args", None)
        params.update(cls_params)

    all_params = {}
    for name, param in params.items():
        annotation = param.annotation
        if annotation is param.empty:
            annotation = (
                type(param.default)
                if param.default is not param.empty
                else annotation
            )

        all_params[name] = NodeAttributeMeta(
            name=name,
            required=param.default is param.empty,
            value=param.default if param.default is not param.empty else None,
            type=_parse_param_type(annotation),
            choices=_get_choices(annotation),
        )

    return all_params
