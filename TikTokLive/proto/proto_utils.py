import re
from typing import List, Tuple, Optional

from TikTokLive.proto import User, BadgeStruct, CommonMessageData


def common_display_type(common: Optional[CommonMessageData]) -> str:
    """Safely read ``common.display_text.key`` through the v3 nullable chain.

    v2 exposed this as ``display_text.display_type``; v3 renamed Text field 1
    (same wire number, same string type) to ``key``.
    """

    if common is None or common.display_text is None:
        return ""
    return common.display_text.key or ""


_BADGE_ONEOF_FIELDS = ("str", "text", "image", "combine")


def _badge_kind(badge: BadgeStruct) -> Optional[str]:
    """Return which oneof field of ``badgeType`` is populated, or None.

    betterproto2 exposes oneof state via ``Message.is_set(field_name)``;
    we walk the four ``badgeType`` members and return the first one set.

    """

    for field_name in _BADGE_ONEOF_FIELDS:
        if badge.is_set(field_name):
            return field_name
    return None


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

    v2 represents badge contents as a ``betterproto2`` oneof under the
    ``badgeType`` group (``image``/``text``/``str``/``combine``).

    """

    kind = _badge_kind(badge)

    # ``_badge_kind`` only returns the field name when ``is_set`` confirms it,
    # so the typed-Optional accesses below are safe at runtime; the asserts
    # narrow for the type checker.

    if kind == "str":
        assert badge.str is not None
        return p.search(badge.str.str)

    if kind == "text":
        assert badge.text is not None
        return p.search(badge.text.default_pattern)

    if kind == "image":
        assert badge.image is not None and badge.image.image is not None
        for image_url in badge.image.image.url_list:
            match = p.search(image_url)
            if match:
                return match
        return None

    if kind == "combine":
        assert badge.combine is not None
        if badge.combine.str:
            match = p.search(badge.combine.str)
            if match:
                return match
        if badge.combine.icon is not None:
            for image_url in badge.combine.icon.url_list:
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
