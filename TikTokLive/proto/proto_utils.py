import re
from typing import List, Tuple, Optional

from TikTokLive.proto import User, BadgeStruct, BadgeStructBadgeDisplayType


def badge_match_user(user: User, p: re.Pattern) -> List[Tuple[re.Match, BadgeStruct]]:
    """
    Search a user's badges for a given regex pattern, and return the matches

    :rtype: object
    :param user: The user to analyze
    :param p: The pattern to check with
    :return: List of matches & their associated badge

    """

    badge_matches: List[Tuple[re.Match, BadgeStruct]] = []

    for badge in user.badge_list:

        found_match: Optional[re.Match] = badge_match(
            badge=badge,
            p=p
        )

        if found_match is not None:
            badge_matches.append(
                (
                    found_match,
                    badge
                )
            )

    return badge_matches


def badge_match(badge: BadgeStruct, p: re.Pattern) -> Optional[re.Match]:
    """
    Complex utility function to search & extract text from ANY type of TikTok badge

    :param badge: The badge to check
    :param p: The pattern to check against
    :return: Matches in the string

    """

    if badge.display_type == BadgeStructBadgeDisplayType.BADGEDISPLAYTYPE_STRING:
        match: Optional[re.Match] = p.search(string=badge.str.str)
        return match

    if badge.display_type == BadgeStructBadgeDisplayType.BADGEDISPLAYTYPE_TEXT:
        match: Optional[re.Match] = p.search(string=badge.text.default_pattern)
        return match

    if badge.display_type == BadgeStructBadgeDisplayType.BADGEDISPLAYTYPE_IMAGE:

        for image_url in badge.image.image.url_list:
            match: Optional[re.Match] = p.search(string=image_url)
            if match:
                return match

        return None

    if badge.display_type == BadgeStructBadgeDisplayType.BADGEDISPLAYTYPE_COMBINE:

        match: Optional[re.Match] = p.search(string=badge.combine.str)
        if match:
            return match

        for image_url in badge.combine.icon.url_list:
            match: Optional[re.Match] = p.search(string=image_url)
            if match:
                return match

        return None

    return None


SUBSCRIBER_BADGE_PATTERN: re.Pattern = re.compile("/sub_")
MODERATOR_BADGE_PATTERN: re.Pattern = re.compile("moderator", flags=re.IGNORECASE)
TOP_GIFTER_BADGE_PATTERN: re.Pattern = re.compile("/new_top_gifter", flags=re.IGNORECASE)
MEMBER_LEVEL_BADGE_PATTERN: re.Pattern = re.compile("fans_badge_icon_lv(\\d+)_v")
GIFTER_LEVEL_BADGE_PATTERN: re.Pattern = re.compile("grade_badge_icon_lite_lv(\\d+)_v")
