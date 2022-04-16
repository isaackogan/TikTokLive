import asyncio
from typing import Optional, List, Callable, Dict

from TikTokLive import TikTokLiveClient
from TikTokLive.types import FailedConnection
from TikTokLive.types.events import CommentEvent, FollowEvent, ShareEvent, LikeEvent, JoinEvent, GiftEvent, ViewerCountUpdateEvent
from colorama import Fore
from twitchio import Channel, Chatter
from twitchio.ext import commands


class TwitchBot(commands.Bot):

    def __init__(self, twitch_token: str, twitch_prefix: str, twitch_channel: str, tiktok_channel: str, cycle_check: int = 120, queue_cycle: int = 0.7):
        """
        Create TwitchBot object

        :param twitch_token: Token for Twitch Bot
        :param twitch_prefix: Prefix for Twitch Bot
        :param twitch_channel: Channel to subscribe to
        :param tiktok_channel: Channel to watch (Twitch Bot)
        :param cycle_check: How often to attempt livestream connections
        :param queue_cycle: How often to read messages from the TikTok message queue

        """

        self._token: str = twitch_token
        self._prefix: str = twitch_prefix
        self._channel: str = twitch_channel
        self._tiktok_channel: str = tiktok_channel
        self.cycle_check: int = cycle_check
        self.queue_cycle: int = queue_cycle
        self.tiktok_listeners: List[Dict[str, Callable]] = []
        self.viewer_count: List[int] = []
        self.message_queue: List[str] = []
        self.channel: Optional[Channel] = None

        super().__init__(token=self._token, prefix=self._prefix, initial_channels=[self._channel])
        self.tiktok: TikTokLiveClient = TikTokLiveClient(tiktok_channel, **{
            "process_initial_data": False  # Spams cached messages on start, must be disabled
        })

    async def handle_message_queue(self):
        """

        If you send commands/messages only to channels in which you have Moderator or Operator status,
        the rate limit is 100 messages per 30 seconds. For this reason, the bot sends one message every
        half a second (60 messages in 30 seconds). Adjust at your own risk.

        """

        while True:
            if len(self.message_queue) > 0:
                message: str = self.message_queue.pop(0)
                await self.channel.send(message)

            await asyncio.sleep(self.queue_cycle)

    async def start_bot(self) -> bool:
        # Start Twitch
        self.channel = self.get_channel(self._channel)
        if self.channel is None:
            print(f"Twitch Channel @{self._channel} is offline. Bot will cycle restarts every {self.cycle_check} seconds until it is available.")
            return False

        # Start TikTok
        try:
            await self.tiktok.start()
        except FailedConnection:
            print(f"TikTok Channel @{self._tiktok_channel} is offline. Bot will cycle restarts every {self.cycle_check} seconds until it is available.")
            self.tiktok = TikTokLiveClient(self._tiktok_channel)
            return False

        self_chatter: Chatter = self.channel.get_chatter(self.nick)
        if not (self_chatter.is_mod or self_chatter.is_broadcaster):
            print("User", self.nick, "is NOT a moderator. You WILL get blocked for spam if your TikTok stream sends more than 20 messages in 30 seconds")

        return True

    async def event_ready(self):
        """
        On ready event

        """

        attempt: bool = await self.start_bot()

        while not attempt:
            await asyncio.sleep(self.cycle_check)
            attempt: bool = await self.start_bot()

        print(f"Twitch & TikTok bots have started. Logged in as {self.nick} on Twitch, watching @{self._tiktok_channel} on TikTok.")
        self.loop.create_task(self.handle_message_queue())

    @commands.command()
    async def help(self, ctx: commands.Context):
        """
        Help Command
        :param ctx: Help Command
        :return: None

        """

        await ctx.send("Commands: " + ' '.join([f"\"{self._prefix}{cmd}\"" for cmd in self.commands.keys()]))

    @commands.command()
    async def tiktok(self, ctx: commands.Context):
        """
        TikTok command
        :param ctx: TikTok Command
        :return: Value

        """
        if len(self.viewer_count) < 1:
            return await ctx.send("TikTok data has not loaded yet, try again soon :)")

        self.viewer_count = [self.viewer_count[-1]]

        await ctx.send(
            f'Currently {self.viewer_count[-1]:,} viewer{"s" if self.viewer_count[-1] > 1 else ""} on TikTok!. Check out the stream at '
            f'https://www.tiktok.com/@{self.tiktok.room_info.get("owner_user_id")} :D'
        )


bot: TwitchBot = TwitchBot(
    twitch_token="TWITCH_OAUTH_TOKEN",
    twitch_prefix="?",
    twitch_channel="TWITCH_CHANNEL_NAME",
    tiktok_channel="TIKTOK_CHANNEL_NAME"
)


@bot.tiktok.on("follow")
async def on_follow(event: FollowEvent):
    message: str = f"{event.user.uniqueId} 🐺🐺🐺🐺🐺🐺🐺followed!🐺🐺🐺🐺🐺🐺🐺{event.user.uniqueId}"
    print(message)
    bot.message_queue.append(message)


@bot.tiktok.on("share")
async def on_share(event: ShareEvent):
    message: str = f"{event.user.uniqueId} shared the streamer!"
    print(message)
    bot.message_queue.append(message)


@bot.tiktok.on("comment")
async def on_comment(event: CommentEvent):
    print(f"{Fore.GREEN}{event.user.nickname} said: {event.comment}")
    bot.message_queue.append(f"{event.user.nickname} said: {event.comment}")


@bot.tiktok.on("like")
async def on_like(event: LikeEvent):
    message: str = f"{event.user.uniqueId} liked the stream {event.likeCount} times, there is now {event.totalLikeCount} total likes!"
    print(message)
    bot.message_queue.append(message)


@bot.tiktok.on("join")
async def on_join(event: JoinEvent):
    print(f"{Fore.YELLOW}{event.user.uniqueId}\033[39m joined!")
    bot.message_queue.append(f"{event.user.uniqueId} joined!")


@bot.tiktok.on("gift")
async def on_gift(event: GiftEvent):
    # If it's type 1 and the streak is over
    if event.gift.gift_type == 1 and event.gift.repeat_end == 1:
        print(f"{Fore.RED}{event.user.uniqueId} sent {event.gift.repeat_count}x \"{event.gift.extended_gift.name}\"")
        bot.message_queue.append(f"{event.user.uniqueId} sent {event.gift.repeat_count}x \"{event.gift.extended_gift.name}\"")

    # It's not type 1, which means it can't have a streak & is automatically over
    elif event.gift.gift_type != 1:
        message: str = f"{event.user.uniqueId} sent \"{event.gift.extended_gift.name}\""
        print(message)
        bot.message_queue.append(message)


@bot.tiktok.on("viewer_count_update")
async def on_connect(event: ViewerCountUpdateEvent):
    print(f"{Fore.RED}Received a new viewer count: {event.viewerCount}")
    bot.message_queue.append(f"Received a new viewer count: {event.viewerCount}")


if __name__ == '__main__':
    # Generate a twitch token here: https://twitchapps.com/tmi/
    # The account MUST have moderator or this bot will NOT work
    bot.run()
