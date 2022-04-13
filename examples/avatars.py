import logging
import random
import string
import traceback
from typing import Dict, Optional, List

import aiohttp
from TikTokLive import TikTokLiveClient
from TikTokLive.types import User
from TikTokLive.types.events import CommentEvent


class ProfileImage:
    DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
        "authority": "m.tiktok.com", "scheme": "https", "sec-gcp": "1",
        "accept-encoding": "gzip", "accept-language": "en-US,en;q=0.9", "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors", "sec-fetch-site": "none", "accept": "application/json, text/plain, */*",
        "Connection": 'keep-alive', "'Cache-Control'": 'max-age=0', "Accept": 'text/html,application/json,application/protobuf',
        "'User-Agent'": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        "Referer": 'https://www.tiktok.com/', "Origin": 'https://www.tiktok.com', "Accept-Language": 'en-US,en;q=0.9', "Accept-Encoding": 'gzip, deflate',
    }

    def __init__(self, user: User):
        self.user: User = user

    @staticmethod
    def generate_device_id() -> str:
        """
        Generates a valid device_id for requests

        """

        return "".join([random.choice(string.digits) for _ in range(19)])

    @property
    def url(self) -> str:
        """
        Get their profile picture URL
        :return: The URL

        """

        return self.user.profilePicture.urls[-1]

    async def to_download(self, path: str, custom_headers: dict = {}, proxies: Optional[List] = []) -> bool:
        """
        Download an image to a given file path

        :param proxies: List of proxies (picks a random one)
        :param path: Path to download to
        :param custom_headers: Custom headers if necessary
        :return: Whether it downloaded successfully

        """
        b: Optional[bytes] = await self.to_bytes(custom_headers, proxies)

        try:
            with open(path, 'wb') as file:
                file.write(b)

            return True
        except:
            logging.error(traceback.format_exc() + "\nFailed to save the image to disk")
            return False

    async def to_bytes(self, custom_headers: dict = {}, proxies: Optional[List] = []) -> Optional[bytes]:
        """
        Turn a profile image object to bytes

        :param proxies: List of proxies (picks a random one)
        :param custom_headers: Custom headers if necessary
        :return: Image in bytes

        """

        return await self.__to_bytes(self.url, headers=custom_headers, proxies=proxies)

    async def __to_bytes(self, url: str, headers: dict, proxies: Optional[List[str]]) -> Optional[bytes]:
        """
        Image to bytes

        :param url: URL of image
        :param headers: Headers to request with
        :return: Optional data (if successful)

        """

        device_id = self.generate_device_id()
        headers: dict = {**self.DEFAULT_REQUEST_HEADERS, **headers, **{"tt_webid": device_id, "tt_webid_v2": device_id}}
        proxy: Optional[str] = random.choice(proxies) if proxies and len(proxies) > 0 else None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, headers=headers, proxy=proxy) as request:
                    return await request.read()
        except:
            logging.error(traceback.format_exc() + "\nFailed to download the profile picture image!")
            return None


# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@planlessvids")


@client.on("comment")
async def on_comment(event: CommentEvent):
    await ProfileImage(event.user).to_download(f"RandomDownload.png")


if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
