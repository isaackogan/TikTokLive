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

        :param image: A direct URL string, or an ``ImageModel`` betterproto
            message (uses ``url_list[0]``).
        :return: The fetched image bytes

        """

        if isinstance(image, ImageModel):
            image_url = image.url_list[0]
        else:
            image_url = image

        response: Response = await self._web.get(url=image_url)
        return response.read()
