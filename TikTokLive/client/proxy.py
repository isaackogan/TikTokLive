import enum
import random
from typing import Optional, List


class RotationSetting(enum.Enum):
    """
    Rotation settings for a proxy container

    """

    CONSECUTIVE: int = 1
    """Rotate proxies consecutively, from proxy 0 -> 1 -> 2 -> ...etc."""

    RANDOM: int = 2
    """Rotate proxies randomly, from proxy 0 -> 69 -> 420 -> 1 -> ...etc."""

    PINNED: int = 3
    """Don't rotate proxies at all, pin to a specific proxy index with set_pinned()"""


class ProxyContainer:

    def __init__(self, *proxies: str, mode: int = 1, enabled: bool = True):
        """
        Create a ProxyContainer object

        :param proxies: *args containing a list of the proxies
        :param mode: The rotation mode as defined in the RotationSetting enum

        """

        self.proxies: List[str] = list(proxies)
        self.__mode: int = mode
        self.__index: int = 0
        self.__pin: int = 0
        self.__before_pinned: int = self.__mode
        self.__enabled: bool = enabled

    @property
    def count(self) -> int:
        """
        Get the current number of proxies in the container

        :return: The current number of proxies

        """

        return len(self.proxies)

    def set_enabled(self, enabled: bool) -> None:
        """
        Set whether the system is enabled

        :param enabled: Whether to pull a proxy on get()
        :return: None

        """

        self.__enabled = enabled

    def set_pinned(self, index: int) -> None:
        """
        Set the proxy rotator to pinned mode in RotationSetting enum
        
        :param index: Index to pin to
        :return: None
        
        """

        self.__pin = index
        self.__before_pinned = self.__mode
        self.__mode = RotationSetting.PINNED

    def set_unpinned(self) -> None:
        """
        Remove pinned status and return to whatever mode was set before set_pinned
        
        :return:None
         
        """

        self.__mode = self.__before_pinned

    def get(self) -> Optional[str]:
        """
        Fetch a proxy using one of the rotation settings defined in RotationSetting

        :return: The HTTP/S proxy to return

        """

        # Has nothing
        if self.count < 1 or not self.__enabled:
            return None

        # Consecutive
        if self.__mode == RotationSetting.CONSECUTIVE:
            index: int = self.__index
            if index >= self.count:
                self.__index, index = 1, 0
            else:
                self.__index += 1

        # Otherwise random
        else:
            index: int = random.randint(0, self.count - 1)

        # Return a proxy
        try:
            return self.proxies[index]
        except IndexError:
            return None
