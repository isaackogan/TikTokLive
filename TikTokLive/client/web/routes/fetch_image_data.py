from typing import Union

from httpx import Response

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.proto import ImageModel


class FetchImageDataRoute(ClientRoute):
    """
    Fetch an image from the TikTok CDN

    """

    async def __call__(self, image: Union[str, ImageModel]) -> bytes:
        """
        Fetch the image from TikTok

        :param image: A betterproto Image message
        :return:

        """

        image_url: str = image.m_urls[0] if isinstance(image, ImageModel) else image
        response: Response = await self._web.get(url=image_url)
        return response.read()
