import base64


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

    @property
    def bytes(self) -> bytes:
        if hasattr(self, 'payload'):
            return self.payload

        return b''

    @property
    def as_base64(self) -> str:
        """
        Base64 encoded bytes

        :return: Base64 encoded bytes

        """

        return base64.b64encode(self.bytes).decode()

    @property
    def size(self) -> int:
        """
        Size of the payload in bytes

        :return: Size of the payload

        """

        return len(self.bytes)
