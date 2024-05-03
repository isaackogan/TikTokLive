from typing import Type, List, cast, Union, get_type_hints, TypedDict, Optional, Dict

import betterproto
import jinja2

import TikTokLive.proto.custom_proto as custom_proto
import TikTokLive.proto.tiktok_proto as tiktok_proto
from TikTokLive.events import Event

EventsList: List[Type[Event]] = cast(Union, Event).__args__

InputClassMapping: Type = TypedDict(
    'InputClassMapping',
    {
        "name": str,
        "mappings": dict[str, Type],
        "super": Optional[Type[betterproto.Message]]
    }
)

InputEnumMapping: Type = TypedDict(
    'InputEnumMapping',
    {
        "name": str,
        "mappings": dict[str, int]
    }
)

PrimitiveMappings: Dict[Type, str] = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    bytes: "unknown"
}


def process_event_class(c: Type[Event]) -> InputClassMapping:
    """
    Generate a type def of an event

    :param c: The event class to check
    :return: The type def

    """

    base_message = None
    for base in c.__bases__:
        if issubclass(base, betterproto.Message):
            base_message = base

    bases_hints = get_type_hints(base_message) if base_message else {}
    mappings: dict[str, Type] = {}

    for member_name, member_type in get_type_hints(c).items():

        if member_name.startswith("_"):
            continue

        if member_name in bases_hints and member_type == bases_hints[member_name]:
            continue

        mappings[member_name] = member_type

    return {'mappings': mappings, 'super': base_message, 'name': c.__name__}


def process_proto_class(c: Type[betterproto.Message]) -> InputClassMapping:
    mappings: dict[str, Type] = {}

    # Look for instances of subclassing
    base_message = None
    for base in c.__bases__:
        if base != betterproto.Message:
            base_message = base

    bases_hints = get_type_hints(base_message) if base_message else {}

    for member_name, member_type in get_type_hints(c).items():

        if member_name.startswith("_"):
            continue

        if member_name in bases_hints and member_type == bases_hints[member_name]:
            continue

        mappings[member_name] = member_type

    return {'mappings': mappings, 'super': base_message, 'name': c.__name__}


def process_proto_enum(c: Type[betterproto.Enum]) -> InputEnumMapping:
    return {
        'mappings': {member.name: member.value for member in c},
        'name': c.__name__
    }


def module_classes(module) -> List[Type]:
    md = module.__dict__
    return [
        md[c] for c in md if (
                isinstance(md[c], type) and md[c].__module__ == module.__name__
        )
    ]


def build_ts_defs(
        enums: List[InputEnumMapping],
        classes: List[InputClassMapping],
        events: List[InputClassMapping],
        primitives: Dict[Type, str]
) -> str:
    env: jinja2.Environment = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=jinja2.FileSystemLoader('./'),
    )

    template = jinja2.Template = env.get_template('ts_template.jinja2')

    return template.render({
        'enums': enums,
        'classes': classes,
        'events': events,
        'primitives': primitives
    })


if __name__ == '__main__':

    all_proto: list[Type] = [
        *module_classes(tiktok_proto),
        *module_classes(custom_proto)
    ]

    enum_defs: list[InputEnumMapping] = []
    class_defs: list[InputClassMapping] = []

    for class_meta in all_proto:

        if issubclass(class_meta, betterproto.Enum):
            enum_defs.append(
                process_proto_enum(class_meta)
            )

        if issubclass(class_meta, betterproto.Message):
            class_defs.append(
                process_proto_class(class_meta)
            )

    event_defs: list[InputClassMapping] = []

    for class_meta in EventsList:
        event_defs.append(
            process_event_class(class_meta)
        )

    with open("./package/index.d.ts", "w") as file:
        file.write(build_ts_defs(
            enums=enum_defs,
            classes=class_defs,
            events=event_defs,
            primitives=PrimitiveMappings
        ))
