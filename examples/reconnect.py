from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import ConnectEvent, DisconnectEvent, LiveEndEvent

# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@jakeandrich")
client.live_ended = False


@client.on("connect")
async def on_connect(_: ConnectEvent):
    print("Connected to Room ID:", client.room_id)


@client.on("live_end")
async def on_live_end(_: LiveEndEvent):
    # If the live ended on its own, you probably don't want to reconnect
    client.live_ended = True


@client.on("disconnect")
async def on_disconnect(event: DisconnectEvent):
    # If webcast_closed is True, TikTok cut the connection & we should try to reconnect
    if event.webcast_closed and not client.live_ended:
        await client.reconnect()


if __name__ == '__main__':
    client.run()
