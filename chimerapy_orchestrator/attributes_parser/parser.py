import enum
import inspect
import typing
from typing import get_args, get_origin, get_type_hints

import chimerapy as cp
from pydantic import BaseModel, Field


class TypeInfo(BaseModel):
    type: str
    items_type: typing.Optional[typing.Union[typing.List[str], str]]

    class Config:
        arbitrary_types_allowed = True
        allow_extra = False


class Argument(BaseModel):
    name: str
    value: typing.Optional[typing.Any] = Field(
        default=None, description="The value of the argument.", alias="default"
    )
    type_info: TypeInfo

    class Config:
        arbitrary_types_allowed = True
        allow_extra = False
        allow_population_by_field_name = True


PRIMITIVE_TYPES = {
    int: {
        "type": "Integer",
    },
    float: {
        "type": "Float",
    },
    str: {
        "type": "String",
    },
    bool: {
        "type": "Boolean",
    },
    bytes: {
        "type": "Bytes",
    },
    tuple: {
        "type": "Tuple",
    },
    list: {
        "type": "List",
    },
    dict: {
        "type": "Dict",
    },
    set: {
        "type": "Set",
    },
    frozenset: {
        "type": "FrozenSet",
    },
    complex: {
        "type": "Complex",
    },
    type(None): {
        "type": "None",
    },
    type(Ellipsis): {
        "type": "Ellipsis",
    },
    type(NotImplemented): {
        "type": "NotImplemented",
    },
    type(...): {
        "type": "Ellipsis",
    },
}


def get_types_hint(  # noqa: C901
    constructor_func,
) -> typing.Dict[str, typing.Any]:
    """Returns type hint of a constructor function"""
    types = {}
    for name, type_ in get_type_hints(constructor_func).items():
        if type_ in PRIMITIVE_TYPES:
            types[name] = {"type": PRIMITIVE_TYPES[type_]["type"]}

        elif get_origin(type_) is typing.Union:
            types[name] = {"type": "Union", "items_type": []}
            for arg in get_args(type_):
                if arg in PRIMITIVE_TYPES:
                    types[name]["items_type"].append(
                        PRIMITIVE_TYPES[arg]["type"]
                    )
                else:
                    types[name]["items_type"].append(str(arg))

        elif get_origin(type_) == get_origin(typing.List):
            arg = get_args(type_)[0]
            if arg in PRIMITIVE_TYPES:
                types[name] = {
                    "type": "List",
                    "items_type": PRIMITIVE_TYPES[arg]["type"],
                }
            else:
                types[name] = {"type": "List", "items_type": "any"}

        elif get_origin(type_) == get_origin(typing.Set):
            arg = get_args(type_)[0]
            if arg in PRIMITIVE_TYPES:
                types[name] = {
                    "type": "Set",
                    "items_type": PRIMITIVE_TYPES[arg]["type"],
                }
            else:
                types[name] = {"type": "Set", "items_type": "any"}

        elif get_origin(type_) == get_origin(typing.Tuple):
            args = get_args(type_)
            types[name] = {"type": "Tuple", "items_type": []}
            for arg in args:
                if arg in PRIMITIVE_TYPES:
                    types[name]["items_type"].append(
                        PRIMITIVE_TYPES[arg]["type"]
                    )
                else:
                    types[name]["items_type"].append(str(arg))

        elif get_origin(type_) == get_origin(typing.Dict):
            types[name] = {
                "type": PRIMITIVE_TYPES[dict]["type"],
            }

        elif get_origin(type_) == typing.Literal:
            types[name] = {"type": "Literal", "items_type": get_args(type_)}

        elif type(type_) == enum.EnumMeta:
            types[name] = {
                "type": "Enum",
                "items_type": [e.name for e in type_],
            }

        else:
            types[name] = {"type": str(type_)}

    return types


def parse_constructor(  # noqa: C901
    class_: typing.Type, follow_superclass=True
) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    """
    Parse the constructor of a class and return argument names and default values with their types (if possible)

    Parameters:
    ----------
    class_:
        The class to parse
    follow_superclass:
        If True, parse the constructor of the superclass as well
    """
    kwargs = {}

    if follow_superclass:
        for superclass in class_.__bases__:
            kwargs.update(parse_constructor(superclass))

    constructor = inspect.signature(class_.__init__)
    parameters = constructor.parameters
    for name, parameter in parameters.items():
        if name == "self":
            continue
        if name == "args":
            continue
        if name == "kwargs":
            continue

        if parameter.default is not inspect.Parameter.empty:
            kwargs[name] = {"default": parameter.default, "name": name}
        else:
            kwargs[name] = {"default": None, "name": name}

    hints = get_types_hint(class_.__init__)

    for key, value in kwargs.items():
        if key in hints:
            value["type_info"] = hints[key]
        else:
            if type(value["default"]) in PRIMITIVE_TYPES:

                value["type_info"] = {
                    "type": PRIMITIVE_TYPES[type(value["default"])]["type"]
                }
            else:
                value["type_info"] = {"type": "String"}

    return kwargs


def get_node_arguments(
    node_class: typing.Type[cp.Node],
) -> typing.Dict[str, Argument]:
    """Get arguments and type info for a chimerapy node."""
    if not issubclass(node_class, cp.Node):
        raise TypeError(f"{node_class} is not a chimerapy node.")

    args = {
        "name": Argument(
            name="name",
            value=node_class.__name__,
            type_info={
                "type": "String",
            },
        ),
        "debug_port": Argument(
            name="debug_port",
            value=None,
            type_info={"type": "Union", "items_type": ["None", "Integer"]},
        ),
        "logdir": Argument(
            name="logdir",
            value=None,
            type_info={"type": "Union", "items_type": ["String", "None"]},
        ),
    }

    node_args = parse_constructor(node_class, follow_superclass=False)
    node_args = {
        name: Argument.parse_obj(value) for name, value in node_args.items()
    }

    args.update(node_args)

    return args
