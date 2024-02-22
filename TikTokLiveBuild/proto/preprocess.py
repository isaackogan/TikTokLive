from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, List, Generator, Union

from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel

logger: logging.Logger = TikTokLiveLogHandler.get_logger(level=LogLevel.INFO)


class PreprocessChain:
    """Allow chained preprocessing methods for greater code clarity"""

    def __init__(self, text: str = ""):
        self.__text: str = text

    def __str__(self) -> str:
        return self.__text

    def append(self, text: Union[PreprocessChain, str], *fns: Callable[[str], str]) -> PreprocessChain:
        for func in fns:
            text = func(text)

        self.__text += text
        return self

    def apply(self, fn: Callable[[str], str]) -> PreprocessChain:
        self.__text = fn(self.__text)
        return self


def find_proto_files(source_dir: Path) -> Generator[Path, None, None]:
    """
    Scan a directory for *.proto files
    :param source_dir: Input directory
    :return: None

    """

    for file in os.listdir(str(source_dir)):
        if file.endswith(".proto"):
            yield source_dir.joinpath(file)


def strip_proto_comments(text_line: str) -> str:
    """
    Remove comments line of a protobuf file
    :param text_line: The line in question
    :return: Replacement string

    """

    comment_idx: int = text_line.find("//")

    if comment_idx >= 0:
        return text_line[:comment_idx]
    return text_line


def convert_proto_int_maps(text_line: str) -> str:
    """
    Naively convert map<int32, any> to map<str, any> as betterproto/python can't hash ints as keys in dicts.

    :param text_line: Line to process
    :return: Processed line

    """

    return text_line.replace("map<int32", "map<string")


def remove_proto_package(text_line: str) -> str:
    """
    Naively removed package specification from a file text line because it breaks the compiler

    :param text_line: The line to remove it from
    :return: Line without the package

    """

    if not text_line.startswith("package"):
        return text_line

    return text_line[text_line.find(";") + 1:]


def pre_process_proto_file(fp_in: Path, dir_out: Path) -> Path:
    """
    Preprocess a proto file for betterproto building

    :param fp_in: Proto file to read
    :param dir_out: Where to drop the output
    :return: None

    """

    processed_text: PreprocessChain = PreprocessChain()
    fp_out: Path = dir_out.joinpath(fp_in.name)

    with open(file=fp_in, mode="r", encoding="utf-8") as file:
        for unprocessed_line in file:
            processed_text.append(
                unprocessed_line,
                strip_proto_comments,
                convert_proto_int_maps,
                remove_proto_package
            )

    with open(file=fp_out, mode="w", encoding='utf-8') as file:
        file.write(str(processed_text))

    return fp_out


def pre_process_proto_dir(dir_in: Path, dir_out: Path) -> List[Path]:
    """
    Preprocess a directory of proto for betterproto building

    :param dir_in: Input directory
    :param dir_out: Output directory
    :return: Files created in the process

    """

    files_created: List[Path] = []

    logger.info(f"Pre-processing files in the '{dir_in.name}' directory.")
    for fp_in in find_proto_files(source_dir=dir_in):
        files_created.append(
            pre_process_proto_file(
                fp_in=fp_in,
                dir_out=dir_out
            )
        )

        logger.info(f"Pre-processed file '{fp_in.name}' successfully.")

    logger.info(f"Pre-processed all files into the '{dir_out.name}' directory.")
    return files_created


if __name__ == '__main__':
    """Preprocess a *.proto file for betterproto build tooling."""

    src_dir: Path = Path(__file__).parent.joinpath("src").resolve()
    dist_dir: Path = Path(__file__).parent.joinpath("dist").resolve()

    pre_process_proto_dir(
        dir_in=src_dir,
        dir_out=dist_dir
    )
