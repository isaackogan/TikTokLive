import logging
import os
import subprocess
from pathlib import Path
from subprocess import CompletedProcess
from typing import List

from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel

logger: logging.Logger = TikTokLiveLogHandler.get_logger(level=LogLevel.INFO)


def build_compiler_command(out_dir: Path, in_fn: str) -> List[str]:
    return (
        [
            "protoc",
            "-I.",
            f"--python_betterproto_out={out_dir}",
            in_fn
        ]
    )


def compile_proto_python(in_fp: Path, out_fd: Path, out_fn: str):
    logger.info("Beginning proto compile script...")

    # Get workdir
    source_dir: str = in_fp.parent.name
    logger.info(f"Set working directory: {source_dir}")

    # Get command
    command: List[str] = build_compiler_command(in_fp.parent, in_fp.name)
    logger.info(f"Executing compilation command: {' '.join(command)}")

    # Run the command
    result: CompletedProcess = subprocess.run(command, capture_output=True, cwd=source_dir)

    # Handle failure
    if result.returncode:
        logger.error("Failed to generate proto...")
        raise RuntimeError(result.stderr.decode('utf-8'))

    logger.info("Successfully generated protobuf python classes.")

    # Rename the file to match the requested
    os.replace(in_fp.parent.joinpath("__init__.py"), out_fd.joinpath(out_fn))
    logger.info(f"Successfully moved the protobuf file to '{out_fd}'.")
    logger.info("Finished the protobuf compiler...")

