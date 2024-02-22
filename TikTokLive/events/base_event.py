
class BaseEvent:
    """
    Base event emitted from the TikTokLiveClient

    """

    @property
    def type(self) -> str:
        """
        String representation of the class type

        :return: Class name

        """

        return self.get_type()

    @classmethod
    def get_type(cls) -> str:
        """
        String representation of the class type

        :return: Class name

        """

        return cls.__name__
