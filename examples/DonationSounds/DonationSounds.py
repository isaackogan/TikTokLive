import functools
import os.path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import GiftEvent, FollowEvent
from playsound import playsound


class DonationSoundClient(TikTokLiveClient):
    """
    Donation sound client that overrides the TikTokClient

    """

    def __init__(self, unique_id: str, sound_debug: bool = True, **options):
        """
        Custom donation sound client

        :param unique_id: Unique ID of the user
        :param options: Regular TikTokLive options

        """

        options["enable_extended_gift_info"] = True
        super().__init__(unique_id, **options)

        self.add_listener("gift", functools.partial(self.__play_sound))
        self.__sounds: Dict[str, str] = dict()
        self.sound_debug: bool = sound_debug

    def __play_sound(self, gift: GiftEvent) -> None:
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
            self.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(playsound, sound))
            if self.sound_debug:
                print(f"Played sound \"{sound}\" for gift \"{gift.gift.extended_gift.name}\"")

    def manually_play_sound(self, sound):
        self.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(playsound, sound))

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


client: DonationSoundClient = DonationSoundClient("@theeupcycler", sound_debug=True)


@client.on("follow")
async def on_follow(event: FollowEvent):
    """
    Manually play a sound when someone follows

    :param event: Follow event
    :return: None

    """
    client.manually_play_sound(f"./sounds/enchanted.wav")


if __name__ == '__main__':
    """
    Additional Required Libraries: 
        pip install playsound==1.2.2
    
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
