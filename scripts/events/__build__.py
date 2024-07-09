import logging

from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.proto import User, ExtendedUser
from overrides import InsertOverrides
from transcribe import EventsTranscriber

if __name__ == '__main__':

    logger: logging.Logger = TikTokLiveLogHandler.get_logger(level=LogLevel.INFO)
    logger.info("Starting events transcription...")

    # Transcribe the events
    EventsTranscriber(
        template_dir="./",
        template_name="events_template.jinja2",
        output_path="../../TikTokLive/events/proto_events.py",
        merge_import="TikTokLive.events.proto_events",
        merge_path="../../TikTokLive/events/proto_events.py"
    )()

    logger.info("Starting events class overriding...")

    # Then insert the class overrides
    InsertOverrides(
        event_module="TikTokLive.events.proto_events",
        overrides_module="TikTokLive.proto.custom_proto",
        override_map={
            User: ExtendedUser
        }
    )()
