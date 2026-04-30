import base64
import sys
from typing import Any, Dict, Optional, get_type_hints


class BaseEvent:
    """
    Base event emitted from the TikTokLiveClient

    """

    # Note: a ``type`` ``@property`` previously aliased ``get_type()``, but it
    # collided with v3 proto fields (e.g. ``WebcastCapsuleMessage.type: int``)
    # that subclasses inherit. Use ``get_type()`` directly.

    @classmethod
    def _type_hints(cls) -> Dict[str, Any]:
        """Resolve forward refs in the upstream proto parent's module globals.

        betterproto2's default ``_type_hints`` evaluates type hints against
        ``sys.modules[cls.__module__].__dict__``. For our generated event
        subclasses, ``cls.__module__`` is ``TikTokLive.events.proto_events``,
        which lacks the upstream module-alias names (``__shared__message__``,
        ``__im__``, etc.) that the parent ``Webcast*Message`` class uses in
        its forward-ref strings — so resolution fails.

        We walk the MRO to find the first upstream ``betterproto2.Message``
        subclass (i.e. the proto parent — defined outside our own package)
        and resolve ``cls``'s hints against that module's globals. Critically
        we still pass ``cls`` (not the ancestor) so subclass-level annotation
        overrides (``user: Optional[ExtendedUser]`` in place of the parent's
        ``user: User``) take precedence via Python's MRO.

        Package-agnostic: the only test is ``module not in our package``, so
        future major versions of the upstream proto package work without
        touching this method.
        """

        import betterproto2  # local to avoid circular import at module load

        for ancestor in cls.__mro__[1:]:
            if not isinstance(ancestor, type) or not issubclass(ancestor, betterproto2.Message):
                continue
            if ancestor is betterproto2.Message:
                continue
            ancestor_mod = getattr(ancestor, "__module__", "")
            # Skip our own intermediate classes; we want the first upstream
            # ancestor that owns the forward-ref aliases.
            if ancestor_mod.startswith(__package__.split(".")[0] + "."):
                continue
            return get_type_hints(cls, sys.modules[ancestor_mod].__dict__, {})

        # No upstream proto parent (e.g. a hand-written event like
        # ``ConnectEvent``): fall back to the standard resolution.
        return get_type_hints(cls, sys.modules[cls.__module__].__dict__, {})

    @classmethod
    def get_type(cls) -> str:
        """
        String representation of the class type

        :return: Class name

        """

        return cls.__name__

    @property
    def bytes(self) -> Optional[bytes]:
        if hasattr(self, 'payload'):
            return self.payload

        return None

    @property
    def as_base64(self) -> str:
        """
        Base64 encoded bytes (empty string if no payload)

        :return: Base64 encoded bytes

        """

        return base64.b64encode(self.bytes or b"").decode()

    @property
    def size(self) -> int:
        """
        Size of the payload in bytes

        :return: Size of the payload

        """

        return len(self.bytes) if self.bytes else -1