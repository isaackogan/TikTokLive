from ffmpy import FFmpeg, FFRuntimeError
import datetime
import json
import functools
import os
import signal
from threading import Thread
from pathlib import Path
from typing import Optional, Union
from queue import Queue

from TikTokLive.client.web.web_base import ClientRoute, TikTokHTTPClient
from TikTokLive.client.web.routes.fetch_video import VideoFetchRoute, VideoFetchQuality, VideoFetchFormat

from pathlib import Path

class AudioFetchRoute(VideoFetchRoute):
    """
    Custom route to record the audio stream from TikTok livestreams in real-time
    """

    def __call__(
            self,
            output_fp: Union[Path, str],
            room_info: dict,
            record_for: Optional[int] = -1,
            chunk_duration: int = 10,
            queue: Optional[Queue] = None,
            **kwargs
    ) -> None:
        """
        Record TikTok livestreams audio (threaded)

        :param output_fp: The path to output the recording to
        :param room_info: Room information used to start the recording
        :param record_for: How long to record for (when <= 0, recording is infinite)
        :param chunk_duration: Duration of each audio chunk in seconds
        :param audio_only: Whether to download only audio
        :param output_format: Any format supported by FFmpeg for audio output (e.g. mp3)
        :param kwargs: Other kwargs to pass to FFmpeg
        :return: None
        """

        unique_id: str = room_info['owner']['display_id']
        self._logger.info(f"Attempting to start audio download on stream for '{unique_id}'.")

        # Construct FFmpeg command for audio-only download
        record_time: Optional[str] = f"-t {record_for}" if record_for and record_for > 0 else None
        record_data: dict = json.loads(room_info['stream_url']['live_core_sdk_data']['pull_data']['stream_data'])
        quality: VideoFetchQuality = VideoFetchQuality.LD  # For audio, LD is chosen by default
        record_url_data: dict = record_data['data'][quality.value]['main']
        record_url: str = record_url_data.get(VideoFetchFormat.FLV.value) or record_url_data['flv']

        output_path = Path(output_fp).with_suffix("")  # Ensure output_fp is a Path object and remove suffix
        output_template = str(output_path) + "_%03d.mp3"  # Create output filename template

        self._ffmpeg = FFmpeg(
            inputs={record_url: None},
            outputs={output_template: f"-f segment -segment_time {chunk_duration} -vn -c:a libmp3lame -q:a 2"},
            global_options=["-y", "-loglevel error"]
        )

        # Run FFmpeg command in a separate thread
        self._thread: Thread = Thread(target=functools.partial(self._threaded_recording, unique_id, queue))
        self._thread.start()

        self._logger.info(
            f"Started the audio download to path \"{output_fp}\" for "
            f"duration \"{record_for if record_for and record_for > 0 else 'infinite'}\" seconds "
            f"on user @{unique_id} with chunk duration \"{chunk_duration}\" seconds."
        )

    @property
    def is_recording(self) -> bool:
        """
        Check if the route is currently in use to record the Live

        :return: Recording status

        """

        return self._ffmpeg and self._thread and self._ffmpeg.process

    def start(self, queue: Optional[Queue] = None, **kwargs):
        if queue:
            kwargs["queue"] = queue
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

    def _threaded_recording(self, unique_id: str, queue: Queue) -> None:
        """
        The function to run the recording in a different thread.

        :param unique_id: The unique_id of the recorded user (for logging purposes)
        :return: None

        """

        started_at: int = int(datetime.utcnow().timestamp())

        try:
            self._ffmpeg.run()
            # Update the queue with the name of the audio file
            output_filename = self._ffmpeg._outputs[0].split()[0]  # Get the name of the audio file from FFmpeg command
            queue.put(output_filename)
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