import re
from typing import List, Tuple, Optional

from TikTokLive.proto import User, BadgeStruct


_BADGE_ONEOF_GROUP = "badgeType"


def _badge_kind(badge: BadgeStruct) -> Optional[str]:
    """Return which oneof field of ``badgeType`` is populated, or None."""

    return getattr(badge, "_group_current", {}).get(_BADGE_ONEOF_GROUP)


def badge_match_user(user: User, p: re.Pattern) -> List[Tuple[re.Match, BadgeStruct]]:
    """
    Search a user's badges for a given regex pattern, and return the matches.

    """

    badge_matches: List[Tuple[re.Match, BadgeStruct]] = []

    for badge in getattr(user, "badges", []) or []:
        found_match: Optional[re.Match] = badge_match(badge=badge, p=p)
        if found_match is not None:
            badge_matches.append((found_match, badge))

    return badge_matches


def badge_match(badge: BadgeStruct, p: re.Pattern) -> Optional[re.Match]:
    """
    Search & extract text from any TikTok badge variant.

    v2 represents badge contents as a ``betterproto`` oneof under the
    ``badgeType`` group (``image``/``text``/``str``/``combine``).

    """

    kind = _badge_kind(badge)

    if kind == "str":
        return p.search(badge.str.str)

    if kind == "text":
        return p.search(badge.text.default_pattern)

    if kind == "image":
        for image_url in badge.image.image.url:
            match = p.search(image_url)
            if match:
                return match
        return None

    if kind == "combine":
        if badge.combine.str:
            match = p.search(badge.combine.str)
            if match:
                return match
        for image_url in badge.combine.icon.url:
            match = p.search(image_url)
            if match:
                return match
        return None

    return None


SUBSCRIBER_BADGE_PATTERN: re.Pattern = re.compile("/sub_")
MODERATOR_BADGE_PATTERN: re.Pattern = re.compile("moderator", flags=re.IGNORECASE)
TOP_GIFTER_BADGE_PATTERN: re.Pattern = re.compile("/new_top_gifter", flags=re.IGNORECASE)
MEMBER_LEVEL_BADGE_PATTERN: re.Pattern = re.compile(r"fans_badge_icon_lv(\d+)_v")
GIFTER_LEVEL_BADGE_PATTERN: re.Pattern = re.compile(r"grade_badge_icon_lite_lv(\d+)_v")
