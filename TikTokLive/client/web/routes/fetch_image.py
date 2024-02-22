from typing import Union

from httpx import Response

from TikTokLive.client.web.web_base import WebcastRoute
from TikTokLive.proto import Image


class ImageFetchRoute(WebcastRoute):

    async def __call__(self, image: Union[str, Image]) -> bytes:

        if isinstance(image, Image):
            image: str = image.url_list[0]

        response: Response = await self._web.get_response(
            url=image
        )

        return response.read()
