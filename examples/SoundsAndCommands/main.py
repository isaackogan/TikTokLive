import functools
import os.path
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, Optional, List

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import GiftEvent, CommentEvent, AbstractEvent, FollowEvent, ShareEvent
from gtts import gTTS
from playsound import playsound


class CombinationClient(TikTokLiveClient):
    """
    Donation sound client that overrides the TikTokClient

    """

    @dataclass
    class Context:
        name: str
        args: List[str]
        event: AbstractEvent

    def __init__(self, unique_id: str, sound_debug: bool = True, command_prefix: str = "/", cache_path: str = "./", **options):
        """
        Custom donation sound client

        :param unique_id: Unique ID of the user
        :param options: Regular TikTokLive options

        """

        options["enable_extended_gift_info"] = True
        options["process_initial_data"] = False

        super().__init__(unique_id, **options)

        self.add_listener("gift", functools.partial(self.__play_gift_sound))
        self.add_listener("comment", functools.partial(self._parse_comments))

        self.__sounds: Dict[str, str] = dict()
        self.sound_debug: bool = sound_debug

        if not os.path.isdir(cache_path):
            raise RuntimeError("Folder does not exist at the current cache path")

        self.command_prefix: str = command_prefix
        self.cache_path: str = cache_path

    def __play_gift_sound(self, gift: GiftEvent) -> None:
        """
        Play a sound when a gift is received

        :param gift: The received gift
        :return: None

        """

        sound: Optional[str] = self.__sounds.get(gift.gift.extended_gift.name.lower())
        default: Optional[str] = self.__sounds.get("default")

        if default is not None:
            sound = default

        if sound is not None and os.path.exists(sound):
            self.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(self.play_sound, sound))
            if self.sound_debug:
                print(f"Played sound \"{sound}\" for {gift.gift.repeat_count}x gift \"{gift.gift.extended_gift.name}\" donated by @{gift.user.uniqueId}")

    def set_sounds(self, sounds: dict) -> dict:
        """
        Update sounds with a K,V approach that checks for file existing

        :param sounds: Sound
        :return: New sound dict

        """

        for name, sound in sounds.items():
            if name and sound:
                if not os.path.exists(sound):
                    raise RuntimeError(f"Path \"{sound}\" doesn't exist for \"{name}\"")
                self.__sounds[name.lower()] = sound

            else:
                raise RuntimeError("Invalid name/sound")

        return self.sounds

    def remove_sounds(self, *sounds) -> dict:
        """
        Remove sounds with a given name

        :param sounds: Sounds to remove
        :return: New sound list

        """

        for sound in sounds:
            try:
                del self.__sounds[sound]
            except IndexError:
                pass

        return self.sounds

    @property
    def sounds(self):
        """
        Get current sound dict config

        :return: Sound dict config

        """

        return self.__sounds

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

        self.emit(f"/{_name}", self.Context(name=_name, args=_command[1:], event=event))

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


client: CombinationClient = CombinationClient("@xenasolo", sound_debug=True)


@client.on("/speak")
async def on_cam_command(context: CombinationClient.Context):
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


@client.on("comment")
async def on_comment(event: CommentEvent):
    print(f"@{event.user.uniqueId} -> {event.comment}")


@client.on("follow")
async def on_follow(event: FollowEvent):
    print(f"@{event.user.uniqueId} followed the creator")


@client.on("share")
async def on_share(event: ShareEvent):
    print(f"@{event.user.uniqueId} shared the livestream")

if __name__ == '__main__':
    """
    Additional Required Libraries: 
        pip install playsound==1.2.2
        pip install gTTS
        pip install playsound
        
    Documentation:
        Documentation is provided via docstrings, but, generally speaking.
        Works by setting a sound dictionary that maps specific gifts to sound files,
        then the client simply plays the sound. It's easy. Really, really easy.

    """

    # Set example sound for Rose
    client.set_sounds({
        "rose": "./sounds/enchanted.wav",
        "default": "./sounds/enchanted.wav"
    })

    # Run client
    client.run()
