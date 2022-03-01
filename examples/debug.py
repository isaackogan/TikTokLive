from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import AbstractEvent

# Instantiate the client with debug param as true
client: TikTokLiveClient = TikTokLiveClient(unique_id="@patuda_donbazz", debug=True)


@client.on("debug")
async def on_debug(event: AbstractEvent):
    # Receive the raw, unprocessed event dictionaries
    print("Raw Event Payload:", event.as_dict)


if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
