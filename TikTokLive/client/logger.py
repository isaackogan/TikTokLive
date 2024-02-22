import enum
import logging
import os
import sys
import traceback
from typing import Optional, List, Any, cast, Dict


class LogLevel(enum.Enum):
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    @property
    def value(self) -> int:
        return cast(int, super().value)


class TikTokLiveLogHandler(logging.StreamHandler):
    """A custom logger implementation for TikTokLive"""

    LOGGER_NAME: str = "TikTokLive"
    LOGGER: Optional[logging.Logger] = None
    TIME_FORMAT: str = "%H:%M:%S"

    SPACING: Dict[int, int] = {
        logging.INFO: 1,
        logging.ERROR: 0,
        logging.WARNING: 1,
        logging.DEBUG: 0
    }

    FORMAT: str = "[%(name)s] %(levelname)s from %(stack)s:%(lineno)d — %(message)s"

    def __init__(
            self,
            stream: Optional[Any] = None,
            formatter: Optional[logging.Formatter] = None
    ):
        super().__init__(stream=stream or sys.stderr)
        self.formatter = formatter or logging.Formatter(self.FORMAT, self.TIME_FORMAT)

    @classmethod
    def get_logger(
            cls,
            level: Optional[LogLevel] = None,
            stream: Optional[Any] = None
    ) -> logging.Logger:
        """
        Create a logger or retrieve the existing one

        :param stream: Where to stream to
        :param level: The level to log above
        :return: Instance of new logger

        """

        if cls.LOGGER and not level:
            return cls.LOGGER

        if not cls.LOGGER:
            log_handler: TikTokLiveLogHandler = TikTokLiveLogHandler(stream)
            cls.LOGGER = logging.getLogger(cls.LOGGER_NAME)
            cls.LOGGER.addHandler(log_handler)

        cls.LOGGER.setLevel((level if level is not None else LogLevel.WARNING).value)
        return cls.LOGGER

    @classmethod
    def format_path(cls, record: logging.LogRecord) -> str:
        work_dir: str = os.path.normpath(os.getcwd())
        stack_path: str = os.path.normpath(record.pathname)

        start_location: int = stack_path.find(work_dir)
        if start_location >= 0:
            stack_path = stack_path[start_location + len(work_dir) + 1:]

        path_parts: List[str] = stack_path.split("/")
        finished_parts: List[str] = []

        for idx, part in enumerate(path_parts):

            if not part:
                continue

            if idx + 1 == len(path_parts):
                finished_parts.append(part)
                break

            finished_parts.append(part[0])
        return ".".join(finished_parts)

    def emit(self, record: logging.LogRecord) -> None:
        """Handle emitting from the logger"""

        try:

            # Pre-process
            record.spacing = self.SPACING.get(record.levelno, 0) * " "
            record.stack = self.format_path(record)

            # Format & write
            self.stream.write(self.format(record) + self.terminator)

            # Flush toilet
            self.flush()
        except Exception:
            self.handleError(record)


def test_logs() -> None:
    """Simple test for the logger"""
    logger: logging.Logger = TikTokLiveLogHandler.get_logger(level=LogLevel.DEBUG)

    logger.info("Some information")
    logger.debug("Some debug")
    logger.warning("Some warning")
    logger.error("Some error")

    try:
        raise RuntimeError("An error occurred resulting in you being thrown.")
    except Exception as ex:
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    test_logs()
