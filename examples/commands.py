import functools
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List

from gtts import gTTS
from playsound import playsound

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent


@dataclass
class Context:
    name: str
    args: List[str]
    event: CommentEvent


class TikTokLiveCommandClient(TikTokLiveClient):
    """
    Command System Client that overrides the main client

    """

    def __init__(self, unique_id: str, command_prefix: str = "/", cache_path: str = "./", **options):
        """
        Initialize the command system
        
        :param unique_id: The username of the user
        :param command_prefix: Prefix for commands
        :param options: Normal TikTokLive options
        
        """

        if not os.path.isdir(cache_path):
            raise RuntimeError("Folder does not exist at the current cache path")

        options["process_initial_data"] = False
        super().__init__(unique_id, **options)
        self.command_prefix: str = command_prefix
        self.cache_path: str = cache_path
        self.add_listener("comment", functools.partial(self._parse_comments))

    async def _parse_comments(self, event: CommentEvent):
        """
        Parse comments into commands
        
        :param event: Comment event
        :return: None
        
        """

        # Not a command
        if not event.comment.startswith(self.command_prefix):
            return

        _command: List[str] = event.comment.split(" ")
        _name: str = _command[0].replace(self.command_prefix, "", 1)

        self.emit(f"/{_name}", Context(name=_name, args=_command[1:], event=event))

    @classmethod
    def play_sound(cls, path: str) -> None:
        """
        Play a given sound given a filepath

        :param path: The filepath
        :return: None

        """

        if not os.path.exists(path):
            return

        playsound(path, block=True)

        try:
            os.remove(path)
        except:
            pass

    async def speak(self, text: str):
        _tts: gTTS = gTTS(text=text, lang='en', slow=False)
        _fp: str = self.cache_path + f"{uuid.uuid4()}.mp3"
        _tts.save(_fp)
        self.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(self.play_sound, _fp))


client: TikTokLiveCommandClient = TikTokLiveCommandClient("@amazingviddeos")


@client.on("/speak")
async def on_cam_command(context: Context):
    """
    All commands, regardless of prefix, run on event /<command_name>

    If your prefix is b!, and someone runs b!test, to listen for that command
    you should write @client.on("/test").

    :param context: Command context including command name, args, and the raw CommentEvent
    :return: None

    """

    print(f"Command \"{context.name}\" was run with arguments \"{', '.join(context.args)}\"")

    message: str = " ".join(context.args)
    await client.speak(text=message)


@client.on("/ping")
async def on_ping(context: Context):
    """
    When someone runs the /ping command, choose how to react

    :param context: Context of the command
    :return: None

    """

    reply: str = f"{context.event.user.uniqueId} Pong!"

    print(f"The bot will respond in chat with \"{reply}\"")
    await client.send_message(reply)


if __name__ == '__main__':
    """
    You can find your session ID in the cookies in your browser on TikTok.com
    Put the session ID here to allow people to respond to commands!
    
    """

    client.run(session_id="SESSION_ID_HERE")
