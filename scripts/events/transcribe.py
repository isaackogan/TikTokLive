import importlib
import inspect
from types import ModuleType
from typing import List, get_type_hints, Dict, Optional, Type, Tuple, Generator

import betterproto
import jinja2

from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.proto.tiktok_proto import CommonMessageData

MESSAGE_OVERRIDES: Dict[str, str] = {
    "WebcastMsgDetectMessage": "MessageDetectEvent",
    "WebcastChatMessage": "CommentEvent",
    "WebcastSubNotifyMessage": "SubscribeEvent",
    "WebcastMemberMessage": "JoinEvent"
}

BASE_IMPORTS: List[str] = [
    "from TikTokLive.proto.tiktok_proto import *",
    "from TikTokLive.proto.custom_proto import *",
    "from .base_event import BaseEvent",
    "from typing import Type, Union, Dict"
]


def is_proto_event(name: str, instance: Type[object]) -> bool:

    # Must be a betterproto message
    try:
        if not issubclass(instance, betterproto.Message):
            return False
    except TypeError:
        return False

    # Retrieve hints
    hints: dict = get_type_hints(instance)

    # Must start with "Webcast"
    if not name.startswith("Webcast"):
        return False

    # Only Events have a common
    if not hints.get('base_message'):
        return False

    # Check, just in case...
    if not issubclass(hints['base_message'], CommonMessageData):
        return False

    return True


class EventsTranscriber:

    def __init__(
        self,
        template_dir: str,
        template_name: str,
        output_path: str,
        merge_import: str,
        merge_path: str
    ):

        self._env: jinja2.Environment = jinja2.Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=jinja2.FileSystemLoader(template_dir),
        )

        self._template: jinja2.Template = self._env.get_template(template_name)
        self._output_path: str = output_path
        self._proto_mod: PreviousMod = PreviousMod(merge_import, merge_path)
        self._import_name: str = merge_import

    def __call__(self, *args, **kwargs):

        output: str = self._template.render(**self.build_config())

        with open(self._output_path, "w", encoding="utf-8") as file:
            file.write(output)

        # Reload the file for other scripts
        importlib.reload(importlib.import_module(self._import_name))

    def generate_events(self) -> Generator[dict, None, None]:
        from TikTokLive.proto import tiktok_proto

        for name, item in tiktok_proto.__dict__.items():

            # Must be an event message
            if not is_proto_event(name, item):
                continue

            # Must not be currently registered
            event_name: str = self.event_name(name)

            yield (
                {
                    "class_name": event_name,
                    "proto_name": name,
                    "write_class": not self._proto_mod.exists_class(event_name)
                }
            )

    @classmethod
    def print_changelog(cls, events, existing_classes) -> None:
        new_events: List[str] = [e["class_name"] for e in events if bool(e["write_class"])]
        all_events: List[str] = [e["class_name"] for e in events]
        unregistered_classes: List[str] = [t[0] for t in existing_classes if t[0] not in all_events]

        logger = TikTokLiveLogHandler.get_logger(level=LogLevel.INFO)

        logger.info(f"Merged {len(existing_classes)} Previous: " + (", ".join([e[0] for e in existing_classes] or "N/A")))
        logger.info(f"Added {len(new_events)} New Events: " + (", ".join(new_events) or "N/A"))
        logger.info(f"Logged {len(unregistered_classes)} Unregistered Classes: " + (", ".join(unregistered_classes) or "N/A"))

    def build_config(self) -> dict:

        events: List[dict] = list(self.generate_events())
        imports: List[str] = [*BASE_IMPORTS, *self._proto_mod.filter_imports(BASE_IMPORTS)]
        existing_classes: List[Tuple[str, str]] = list(self._proto_mod.get_classes())

        self.print_changelog(events, existing_classes)

        return {
            "events": events,
            "imports": imports,
            "classes": existing_classes
        }

    @classmethod
    def event_name(cls, subclass_name: str) -> str:

        # Handle Overrides
        if subclass_name in MESSAGE_OVERRIDES:
            return MESSAGE_OVERRIDES[subclass_name]

        if subclass_name.endswith("Message"):
            return subclass_name \
                .replace("Message", "Event") \
                .replace("Webcast", "")
        else:
            return subclass_name \
                .replace("Webcast", "") \
                + "Event"


class PreviousMod:

    def __init__(self, name: str, path: str):
        try:
            self._input: ModuleType = importlib.import_module(name=name)
        except ModuleNotFoundError:
            open(path, mode="w", encoding="utf-8").write("")
            self._input: ModuleType = importlib.import_module(name=name)
        try:
            self._src: str = inspect.getsource(self._input)
        except OSError:
            self._src: str = ""

    def get_class_text(self, class_name: str) -> Optional[str]:
        c: Optional[Type] = getattr(self._input, class_name, None)

        if c is None:
            return None

        return inspect.getsource(c)

    def exists_class(self, class_name: str) -> bool:
        return bool(getattr(self._input, class_name, None))

    def get_classes(self) -> Generator[Tuple[str, str], None, None]:
        input_mod = inspect.getmodule(self._input)

        for name, obj in inspect.getmembers(self._input):

            if inspect.isclass(obj) and inspect.getmodule(obj) == input_mod:
                yield name, inspect.getsource(obj)

    def filter_imports(self, base_imports: List[str]) -> List[str]:
        src_lines: List[str] = self._src.split("\n")
        imports: List[str] = []

        for line in src_lines:

            if "import " not in line:
                continue

            # Check against base imports
            if any([i in line for i in base_imports]):
                continue

            imports.append(line)

        return imports

