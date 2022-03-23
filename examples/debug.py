from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import AbstractEvent, GiftEvent

# Instantiate the client with debug param as true
client: TikTokLiveClient = TikTokLiveClient(unique_id="@tofy_love1", debug=True)


@client.on("gift")
async def on_gift(event: GiftEvent):
    # When gifts are sent
    print(event.user.uniqueId, event.gift.extended_gift.name)


# Only fires when debug is set to True
@client.on("debug")
async def on_debug(event: AbstractEvent):
    # Receive the raw, unprocessed event dictionaries
    if "gift" in event.as_dict.keys():
        print(event.as_dict)


if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
