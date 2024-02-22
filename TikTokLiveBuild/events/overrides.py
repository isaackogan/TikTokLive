import dataclasses
import importlib
import inspect
import logging
from pathlib import Path
from types import ModuleType
from typing import Type, Dict, Generator, Any, Union

import betterproto

from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.events.base import BaseEvent
from TikTokLive.proto import ExtendedUser
from TikTokLive.proto.tiktok_proto import User


TypeToReplace: Type = Type[betterproto.Message]
FieldName: Type = str
ReplacementType: Type = Type[betterproto.Message]
OverrideMap: Type = Dict[TypeToReplace, ReplacementType]
EventOverridesMap: Type = Dict[Type, Dict[FieldName, ReplacementType]]


class InsertOverrides:

    TAB: str = " " * 4

    def __init__(
            self,
            event_module: str,
            overrides_module: str,
            override_map: OverrideMap
    ):
        """
        Automatically insert overrides into the event dataclasses with extended items

        :param event_module: The module containing the proto events
        :param overrides_module: The module containing the overrides
        :param override_map: The map of what should be replaced with what in the events

        """

        self._event_module: ModuleType = importlib.import_module(name=event_module)
        self._overrides_module: ModuleType = importlib.import_module(name=overrides_module)
        self._overrides_module_name: str = overrides_module
        self._override_map: OverrideMap = override_map
        self._logger: logging.Logger = TikTokLiveLogHandler.get_logger(level=LogLevel.INFO)

    def _get_event_classes(self) -> Generator[Any, None, None]:
        for name, obj in inspect.getmembers(self._event_module):
            if inspect.isclass(obj) and issubclass(obj, BaseEvent) and not obj == BaseEvent:
                yield obj

    def build_override_map(self, event: Union[dataclasses.dataclass, BaseEvent]) -> Dict[FieldName, ReplacementType]:
        event_override_map: Dict[FieldName, ReplacementType] = {}

        event_annotations: dict = event.__dict__.get("__annotations__", {})

        for field in dataclasses.fields(event):
            for override, replacement in self._override_map.items():

                # If the field doesn't match the ovverride type
                if str(field.type) != override.__name__:
                    continue

                # If it's already annotated don't include it
                if field.name in event_annotations:
                    continue

                event_override_map[field.name] = replacement

        if len(event_override_map) > 0:
            self._logger.info(f"Found {len(event_override_map)} overrides in {event} class.")

        return event_override_map

    def build_overrides(self) -> EventOverridesMap:
        self._logger.info("Building overrides...")
        event_override_map: EventOverridesMap = {}

        for event in self._get_event_classes():
            overrides = self.build_override_map(event)
            if bool(overrides):
                event_override_map[event] = overrides

        self._logger.info(f"Found new overrides in {len(event_override_map)} classes...")
        return event_override_map

    def build_annotation(self, name: FieldName, replacement: ReplacementType) -> str:
        return f"{self.TAB}{name}: {replacement.__name__}\n"

    def write_overrides(self, overrides: EventOverridesMap):
        path: Path = Path(self._event_module.__file__).resolve()
        file_content: str = open(path, mode="r", encoding="utf-8").read()

        for event, event_overrides in overrides.items():

            if not event.__doc__:
                raise ValueError("Events MUST have a docstring to be found.")

            for field_name, replacement_type in event_overrides.items():
                docstr_end_idx = file_content.find(event.__doc__) + len(event.__doc__)

                start_idx: int = file_content.find(
                    "\n",
                    file_content.find("\n", docstr_end_idx) + 1
                ) + 1

                # update contents
                file_content = (
                        file_content[:start_idx]
                        + self.build_annotation(field_name, replacement_type)
                        + file_content[start_idx:]
                )

        with open(path, mode="w", encoding="utf-8") as file:
            file.write(file_content)
        self._logger.info("Updated overrides successfully")

    def __call__(self) -> None:
        overrides: EventOverridesMap = self.build_overrides()

        if len(overrides) < 1:
            self._logger.info("No new overrides; module was left alone.")
            return

        self.write_overrides(overrides)


if __name__ == '__main__':
    InsertOverrides(
        event_module="TikTokLive.events.proto_events",
        overrides_module="TikTokLive.proto.custom_proto",
        override_map={
            User: ExtendedUser
        }
    )()