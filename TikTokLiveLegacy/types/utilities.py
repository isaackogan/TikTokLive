from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TikTokLive import TikTokLiveClient

from dataclasses import field, dataclass
from typing import Optional

from mashumaro import field_options


def alias(name, **kwargs):
    if 'default_factory' not in kwargs:
        kwargs['default'] = kwargs.get('default') or None
    return field(metadata=field_options(alias=name), **kwargs)


# noinspection PyPep8Naming
def LiveEvent(name):
    def inner(cls):
        cls.name = name
        return dataclass(cls)

    return inner


async def download(url: str, client: TikTokLiveClient) -> Optional[bytes]:
    """
    Download an image from the TikTok API
    :param url: URL for image download
    :param client: TikTokLiveClient with which to download (use its HTTP client)
    :return: The result

    """

    # Make sure there's a URL
    if not url:
        return None

    # Make the request
    return await client.http.get_image_from_tiktok_api(url, client.http.params)
