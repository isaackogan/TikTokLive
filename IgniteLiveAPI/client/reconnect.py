import random
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class ReconnectPolicy:
    """
    How the client recovers when its WebSocket connection drops. Pass an instance (or ``True`` for these defaults)
    as ``reconnect=`` to ``client.start()`` / ``connect()`` / ``run()``.

    A reconnect is a full restart of the connect sequence: the stream is checked to still be live and a fresh signed
    WebSocket URL is requested, because signed URLs expire within about 30 seconds and can never be reused.

    The delay before attempt ``n`` is ``min(max_delay, base_delay * multiplier ** (n - 1))``, randomised by
    ``+/- jitter`` so a fleet of clients that dropped together does not retry in lockstep.

    """

    max_attempts: Optional[int] = 10
    """Consecutive failed attempts before giving up with ``ReconnectFailedError``. ``None`` retries forever."""

    base_delay: float = 2.0
    """Seconds to wait before the first retry."""

    max_delay: float = 60.0
    """Upper bound on the (pre-jitter) delay."""

    multiplier: float = 2.0
    """Growth factor of the delay between consecutive attempts."""

    jitter: float = 0.25
    """Fraction of the delay to randomise by, in either direction (``0`` disables jitter)."""

    stable_after: float = 30.0
    """A connection that stayed up this many seconds counts as healthy and resets the attempt counter."""

    def __post_init__(self) -> None:
        if self.max_attempts is not None and self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1, or None to retry forever")
        if self.base_delay < 0 or self.max_delay < self.base_delay:
            raise ValueError("Require 0 <= base_delay <= max_delay")
        if self.multiplier < 1:
            raise ValueError("multiplier must be at least 1")
        if not 0 <= self.jitter < 1:
            raise ValueError("jitter must be in [0, 1)")
        if self.stable_after < 0:
            raise ValueError("stable_after must not be negative")

    def delay(self, attempt: int, rand: Callable[[], float] = random.random) -> float:
        """
        Seconds to wait before the given (1-based) attempt.

        :param attempt: The attempt number, starting at 1
        :param rand: Source of randomness in [0, 1); injectable for tests
        :return: The delay in seconds

        """

        raw = min(self.max_delay, self.base_delay * self.multiplier ** (max(attempt, 1) - 1))
        return max(0.0, raw * (1 + self.jitter * (2 * rand() - 1)))

    def exhausted(self, attempt: int) -> bool:
        """Whether the (1-based) attempt number exceeds the allowed budget"""
        return self.max_attempts is not None and attempt > self.max_attempts


__all__ = ["ReconnectPolicy"]
