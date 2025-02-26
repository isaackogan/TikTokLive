import enum
import functools
import json
import os
import signal
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Optional, Union

from ffmpy import FFmpeg, FFRuntimeError

from TikTokLive.client.errors import TikTokLiveError
from TikTokLive.client.web.web_base import ClientRoute, TikTokHTTPClient


class VideoFetchFormat(enum.Enum):
    """
    TikTok-supported video recording formats

    """

    FLV = "flv"
    HLS = "hls"
    CMAF = "cmaf"


class VideoFetchQuality(enum.Enum):
    """
    Video quality selection for stream downloads

    """

    LD = "ld"
    """Low definition (480p, vbrate-500,000)"""

    SD = "sd"
    """Standard definition (480p, vbrate-800,000)"""

    HD = "hd"
    """High definition (540p, vbrate-1,000,000)"""

    UHD = "uhd"
    """Ultra-high definition (720p, vbrate-1,000,000)"""

    ORIGIN = "origin"
    """Original definition (N/A, vbrate-N/A)"""


class DuplicateDownloadError(TikTokLiveError):
    """
    Thrown when attempting to start a duplicate download on a video you are already downloading

    """


class FetchVideoDataRoute(ClientRoute):
    """
    TikTok route to record the livestream video in real-time

    """

    def __init__(self, web: TikTokHTTPClient):
        """
        Instantiate the video fetch route

        :param web: The web client used to initialize the route

        """

        super().__init__(web)

        # Storage for the thread / ffmpeg
        self._ffmpeg: Optional[FFmpeg] = None
        self._thread: Optional[Thread] = None
        self._output_fp: Optional[str] = None

    @property
    def ffmpeg(self) -> Optional[FFmpeg]:
        """
        Return a copy of the FFmpeg class, which is only defined while recording

        :return: Copy of the class or None

        """

        return self._ffmpeg

    @property
    def is_recording(self) -> bool:
        """
        Check if the route is currently in use to record the Live

        :return: Recording status

        """

        return bool(self._ffmpeg) and self._thread and self._ffmpeg.process

    @property
    def output_filename(self) -> Optional[str]:
        """
        Get the output filename

        :return: output filename or None

        """

        return self._output_fp

    def __call__(
            self,
            output_fp: Union[Path, str],
            room_info: dict,
            record_for: Optional[int] = -1,
            quality: VideoFetchQuality = VideoFetchQuality.LD,
            record_format: VideoFetchFormat = VideoFetchFormat.FLV,
            output_format: Optional[str] = None,
            **kwargs
    ) -> None:
        """
        Record TikTok livestreams (threaded)

        :param output_fp: The path to output the recording to
        :param room_info: Room information used to start the recording
        :param record_for: How long to record for (when <= 0, recording is infinite)
        :param quality: A `VideoFetchQuality` enum value for one of the supported TikTok qualities
        :param record_format: A `VideoFetchFormat` enum value for one of the supported TikTok formats
        :param output_format: Any format supported by FFmpeg for video output (e.g. mp4)
        :param kwargs: Other kwargs to pass to FFmpeg
        :return: None

        """
        self._output_fp = str(output_fp)

        unique_id: str = room_info['owner']['display_id']
        self._logger.info(f"Attempting to start download on stream for '{unique_id}'.")

        if self._ffmpeg is not None:
            raise DuplicateDownloadError("You are already downloading this stream!")

        record_time: dict = {str(record_for): "-t"} if record_for and record_for > 0 else {}
        record_data: dict = json.loads(room_info['stream_url']['live_core_sdk_data']['pull_data']['stream_data'])
        record_url_data: dict = record_data['data'][quality.value]['main']
        record_url: str = record_url_data.get(record_format.value) or record_url_data['flv']

        self._ffmpeg = FFmpeg(
            inputs={**{record_url: None}, **kwargs.pop('inputs', dict())},
            outputs={
                **{v: k for k, v in kwargs.pop('outputs', dict()).items()},
                **{
                    **record_time,
                    str(output_fp): None,
                    output_format or record_format.value: "-f"
                }
            },
            global_options=(
                list(
                    {"-y", f"-loglevel {kwargs.pop('loglevel', 'error')}"}.union(kwargs.pop('global_options', set()))
                )
            ),
            **kwargs
        )

        self._thread: Thread = Thread(target=functools.partial(self._threaded_recording, unique_id))
        self._thread.start()

        self._logger.info(
            f"Started the download to path \"{output_fp}\" for "
            f"duration \"{record_for if record_for and record_for > 0 else 'infinite'}\" seconds "
            f"on user @{unique_id} with video quality \"{quality.name}\"."
        )

    def start(self, **kwargs) -> None:
        """
        Alias for calling the class itself, starts a recording

        :param kwargs: Kwargs to pass to `__call__`
        :return: None

        """

        self(**kwargs)

    def stop(self) -> None:
        """
        Stop a livestream recording if it is ongoing

        :return: None

        """

        if not self.is_recording:
            self._logger.warning("Attempted to stop a stream that does not exist or has not started.")
            return

        os.kill(self._ffmpeg.process.pid, signal.SIGTERM)

        self._ffmpeg = None
        self._thread = None

    def _threaded_recording(self, unique_id: str) -> None:
        """
        The function to run the recording in a different thread.

        :param unique_id: The unique_id of the recorded user (for logging purposes)
        :return: None

        """

        started_at: int = int(datetime.utcnow().timestamp())

        try:
            self._ffmpeg.run()
        except FFRuntimeError as ex:
            if ex.exit_code and ex.exit_code != 255:
                self._ffmpeg = None
                raise

        finish_time: int = int(datetime.utcnow().timestamp())
        record_time: int = finish_time - started_at

        self._logger.info(
            f"Download stopped for user @\"{unique_id}\" which started at {started_at} and lasted "
            f"for {record_time} second(s)."
        )
