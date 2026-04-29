from typing import Union

from httpx import Response

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.proto import Image, ImageModel


class FetchImageDataRoute(ClientRoute):
    """
    Fetch an image from the TikTok CDN

    """

    async def __call__(self, image: Union[str, Image, ImageModel]) -> bytes:
        """
        Fetch the image from TikTok

        :param image: A direct URL string, or any betterproto image-shaped
            message (``Image`` uses ``url``; ``ImageModel`` uses ``m_urls``).
        :return: The fetched image bytes

        """

        if isinstance(image, ImageModel):
            image_url = image.m_urls[0]
        elif isinstance(image, Image):
            image_url = image.url[0]
        else:
            image_url = image

        response: Response = await self._web.get(url=image_url)
        return response.read()
