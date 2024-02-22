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

from TikTokLive.client.web.web_base import WebcastRoute, WebcastHTTPClient


class VideoFetchFormat(enum.Enum):
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


class DuplicateDownloadError(RuntimeError):
    pass


class VideoFetchRoute(WebcastRoute):

    def __init__(self, web: WebcastHTTPClient):
        super().__init__(web)
        self._ffmpeg: Optional[FFmpeg] = None
        self._thread: Optional[Thread] = None

    def __call__(self, **kwargs) -> None:
        return self.start(**kwargs)

    @property
    def ffmpeg(self) -> Optional[FFmpeg]:
        return self._ffmpeg

    @property
    def recording(self) -> bool:
        return self._ffmpeg and self._thread and self._ffmpeg.process

    def start(
            self,
            output_fp: Union[Path, str],
            room_info: dict,
            record_for: Optional[int] = -1,
            quality: VideoFetchQuality = VideoFetchQuality.LD,
            record_format: VideoFetchFormat = VideoFetchFormat.FLV,
            output_format: Optional[str] = None,
            unique_id: Optional[str] = None,
            **kwargs
    ) -> None:
        unique_id: str = unique_id or self._web.unique_id
        self._logger.info(f"Attempting to start download on stream for '{unique_id}'.")

        if self._ffmpeg is not None:
            raise DuplicateDownloadError("You are already downloading this stream!")

        record_time: Optional[str] = f"-t {record_for}" if record_for and record_for > 0 else None
        record_data: dict = json.loads(room_info['stream_url']['live_core_sdk_data']['pull_data']['stream_data'])
        record_url_data: dict = record_data['data'][quality.value]['main']
        record_url: str = record_url_data.get(record_format) or record_url_data['flv']

        self._ffmpeg = FFmpeg(
            inputs={**{record_url: None}, **kwargs.get('inputs', dict())},
            outputs={
                **{
                    str(output_fp): record_time,
                    output_format or record_format.value: "-f"
                },
                **kwargs.get('outputs', dict())
            },
            global_options=(
                {"-y", f"-loglevel {kwargs.get('loglevel', 'error')}"}
                .union(kwargs.get('global_options', set()))
            ),
        )

        self._thread: Thread = Thread(target=functools.partial(self._threaded_recording, unique_id))
        self._thread.start()

        self._logger.info(
            f"Started the download to path \"{output_fp}\" for "
            f"duration \"{record_for if record_for and record_for > 0 else 'infinite'}\" seconds "
            f"on user @{unique_id} with video quality \"{quality.name}\"."
        )

    def stop(self) -> None:

        if not self.recording:
            self._logger.warning("Attempted to stop a stream that does not exist or has not started.")
            return

        os.kill(self._ffmpeg.process.pid, signal.SIGTERM)

        self._ffmpeg = None
        self._thread = None

    def _threaded_recording(self, unique_id: str) -> None:
        """The function to run the recording in a different thread."""

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
