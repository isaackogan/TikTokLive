from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TikTokLive import TikTokLiveClient

import base64
from dataclasses import field
from typing import Optional, List, Any, Dict, ClassVar

from mashumaro import DataClassDictMixin, pass_through

from TikTokLive.types import User, Gift, Emote, TreasureBoxData, ExtraRankData, LinkUser, BattleArmy
from TikTokLive.types.utilities import LiveEvent, alias


class AbstractEvent(DataClassDictMixin):
    """
    Abstract TikTok Live event from which to build on

    """

    name: ClassVar[str] = "event"
    """The name of the TikTokLive event"""

    def __init__(self):
        """
        Never run, this method is for type hinting the raw_data attribute

        """

        self.raw_data: Optional[dict] = dict()
        """Raw event data as a dictionary in-case the dataclasses miss something"""

    def _forward_client(self, client: TikTokLiveClient):
        """
        Forward the client to events where it is required

        """

        if hasattr(self, "user") and isinstance(self.user, User):
            self.user.avatar._client = client
            for badge in self.user.badges:
                for image_badge in badge.image_badges:
                    image_badge._client = client


@LiveEvent("connect")
class ConnectEvent(AbstractEvent):
    """
    Event that fires when the client connect to a livestream
    
    """


@LiveEvent("disconnect")
class DisconnectEvent(AbstractEvent):
    """
    Event that fires when the client disconnects from a livestream
    
    """


@LiveEvent("like")
class LikeEvent(AbstractEvent):
    """
    Event that fires when a user likes the livestream
    
    """

    user: Optional[User] = None
    """The user that liked the stream"""

    likes: Optional[int] = None
    """The number of likes sent in the payload (Max: 15)"""

    total_likes: Optional[int] = None
    """Total number of likes sent"""

    display_type: Optional[str] = None
    """Internal type"""

    label: Optional[str] = None
    """Internal TikTok label"""


@LiveEvent("join")
class JoinEvent(AbstractEvent):
    """
    Event that fires when a user joins the livestream
    
    """

    user: Optional[User] = None
    """The user that joined the stream"""

    display_type: Optional[str] = None
    """The type of event"""

    label: Optional[str] = None
    """Label for event in live chat"""

    action_id: Optional[int] = None
    """Internal action ID from TikTok"""

    @property
    def through_share(self) -> bool:
        """
        Whether they joined through a link vs. the TikTok App

        :return: Returns True if they joined through a share link

        """
        return self.type == "pm_mt_join_message_other_viewer"


@LiveEvent("follow")
class FollowEvent(AbstractEvent):
    """
    Event that fires when a user follows the livestream
    
    """

    user: Optional[User] = None
    """The user that followed the streamer"""

    display_type: Optional[str] = None
    """Internal TikTok display type"""

    label: Optional[str] = None
    """Internal TikTok label"""


@LiveEvent("share")
class ShareEvent(AbstractEvent):
    """
    Event that fires when a user shares the livestream

    """

    user: Optional[User] = None
    """The user that shared the stream"""

    display_type: Optional[str] = None
    """Internal TikTok display type"""

    label: Optional[str] = None
    """Internal TikTok label"""


@LiveEvent("more_share")
class MoreShareEvent(ShareEvent):
    """
    Event that fires when a user shared the livestream to more than 5/10 users
    e.g. "user123 has shared to more than 10 people!"

    """

    @property
    def amount(self) -> Optional[int]:
        """
        The number of people that have joined the stream off the user

        :return: The number of people that have joined

        """

        try:
            return int(self.display_type.split("pm_mt_guidance_viewer_")[1].split("_share")[0])
        except IndexError:
            return None


@LiveEvent("viewer_count")
class ViewerCountEvent(AbstractEvent):
    """
    Event that fires when the viewer count for the livestream updates
    
    """

    viewer_count: Optional[int] = None
    """The number of people viewing the stream currently"""


@LiveEvent("comment")
class CommentEvent(AbstractEvent):
    """
    Event that fires when someone comments on the livestream
    
    """

    user: Optional[User] = None
    """The user that sent the comment"""

    comment: Optional[str] = None
    """The UTF-8 text comment that was sent"""


@LiveEvent("live_end")
class LiveEndEvent(AbstractEvent):
    """
    Event that fires when the livestream ends
    
    """


@LiveEvent("gift")
class GiftEvent(AbstractEvent):
    """
    Event that fires when a gift is received
    
    """

    user: Optional[User] = None
    """The user that sent the gift"""

    gift: Optional[Gift] = None
    """Object containing gift data"""

    def _forward_client(self, client: TikTokLiveClient):
        """
        Forward the client to events where it is required

        """

        super()._forward_client(client)

        if hasattr(self, "gift") and isinstance(self.gift, Gift):
            if self.gift.info:
                self.gift.info.image._client = client
            if self.gift.detailed:
                self.gift.detailed.icon._client = client

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        De-flatten the gift event (too much in the primary payload)

        """

        d["gift"] = d  # Move 'er up a bit
        return d


@LiveEvent("question")
class QuestionEvent(AbstractEvent):
    """
    Event that fires when someone asks a Q&A question
    
    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Flatten the question event a bit

        """

        d = d.get("questionDetails")  # Get rid of empty container
        return d

    question: Optional[str] = None
    """The question that was asked"""

    user: Optional[User] = None
    """User who asked the question"""


@LiveEvent("emote")
class EmoteEvent(AbstractEvent):
    """
    Event that fires when someone sends a subscriber emote
    
    """

    def _forward_client(self, client: TikTokLiveClient):
        """
        Forward the client to events where it is required

        """

        super()._forward_client(client)

        if hasattr(self, "emote") and isinstance(self.emote, Emote):
            self.emote.image._client = client

    user: Optional[User] = None
    """Person who sent the emote message"""

    emote: Optional[Emote] = None
    """The emote the person sent"""


@LiveEvent("envelope")
class EnvelopeEvent(AbstractEvent):
    """
    Event that fire when someone sends an envelope (treasure box)
    
    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Get rid of an obscene amount of nesting in the envelope event

        """

        # holy crap
        user_3: List[dict] = d.get("treasureBoxUser", dict()).get("user2", dict()).get("user3", list())
        d["treasureBoxUser"] = (user_3[0].get('user4', dict()).get('user', None)) if len(user_3) > 0 else None
        return d

    treasure_box_data: Optional[TreasureBoxData] = alias('treasureBoxData')
    """Data about the enclosed Treasure Box in the envelope"""

    treasure_box_user: Optional[User] = alias('treasureBoxUser')
    """Data about the user that sent the treasure box"""


@LiveEvent("weekly_ranking")
class WeeklyRankingEvent(AbstractEvent):
    """
    Event that fires when the weekly rankings are updated

    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Pre-process weekly ranking event

        """

        ranks: Dict[str, Any] = d.get('data', dict()).get('rankings', dict())  # Do a little flattening

        # Try to flatten rank data & convert to int
        try:
            ranks['rank'] = int(ranks.get('data', dict()).get('rank', None))
        except:
            pass

        return ranks

    type: Optional[str] = None
    """Unknown"""

    label: Optional[str] = None
    """Internal TikTok Label"""

    extra: Optional[ExtraRankData] = field(default_factory=lambda: ExtraRankData())
    """Extra data relating to the UI, presumably"""

    rank: Optional[int] = None
    """The number for the user's TikTok ranking. If the rank is "None", the user is not in the top 99."""

    @property
    def top_99(self) -> bool:
        """
        Whether the user is in the top 99 of creators
        """

        return self.rank is not None


@LiveEvent("intro_message")
class IntroMessageEvent(AbstractEvent):
    """
    Event fires giving the current stream description when the stream is joined
    Note: Only fires if "process_initial_data" is enabled and the streamer has an intro message configured

    """

    room_id: Optional[int] = None
    """Room ID of the room we are in"""

    message: Optional[str] = None
    """The pinned intro message in the livestream"""

    streamer: Optional[User] = None
    """User payload of information about the streamer"""


@LiveEvent("mic_battle_start")
class MicBattleStartEvent(AbstractEvent):
    """
    Event that fires when a Mic Battle starts

    """

    def _forward_client(self, client: TikTokLiveClient):
        """
        Forward the client to events where it is required

        """

        if hasattr(self, "battle_users") and isinstance(self.battle_users, list):
            for user in self.battle_users:
                if isinstance(user, LinkUser):
                    user.avatar._client = client

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Re-structure messy TikTok structuring for battles

        """

        # Flatten the nested TikTok structures into just a list of LinkUsers
        battle_users: List[LinkUser] = []
        for user_data in d.get('battleUsers', list()):
            try:
                battle_users.append(user_data["battleGroup"]["user"])
            except KeyError:
                continue

        return {'battle_users': battle_users}

    battle_users: List[LinkUser] = field(default_factory=lambda: [])
    """Information about the users engaged in the Mic Battle"""


@LiveEvent("mic_battle_update")
class MicBattleUpdateEvent(AbstractEvent):
    """
    Triggered every time a battle participant receives points.
    Contains the current status of the battle and the army that supported the group.

    """

    def _forward_client(self, client: TikTokLiveClient):
        """
        Forward the client to events where it is required

        """

        if hasattr(self, "battle_armies") and isinstance(self.battle_armies, list):
            for army in self.battle_armies:
                for user in army.participants:
                    if isinstance(user, User):
                        user.avatar._client = client

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        This event needs to be entirely custom-handled because it's a mess on TikTok's end

        """

        event_data: dict = {'battle_status': d.get('battleStatus')}
        battle_armies: list = []

        for battle_item in d.get('battleItems', list()):
            for battle_group in battle_item.get('battleGroups', list()):
                battle_armies.append({
                    'host_user_id': battle_item.get('hostUserId'),
                    'points': battle_group.get('points') or None,
                    'participants': battle_group.get('users') or list()
                })

        event_data['battle_armies'] = battle_armies
        return event_data

    battle_status: Optional[int] = None
    """The status of the current Battle. If battle_status=1, the battle is ongoing. If it's 2, the battle has ended."""

    battle_armies: List[BattleArmy] = field(default_factory=lambda: [])
    """Information about the users engaged in the Mic Battle"""

    @property
    def in_battle(self) -> bool:
        """
        Whether the users are currently in battle

        """

        return self.battle_status == 1

    @property
    def battle_finished(self) -> bool:
        """
        Whether the battle is currently finished

        """

        return self.battle_status == 2


@LiveEvent("unknown")
class UnknownEvent(AbstractEvent):
    """
    Event that fires when an event is received that is missing a handler

    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Give *some* structure for unknown events. We're not savages, here.

        """

        # Shallow copy of the data
        copy: Dict[Any, Any] = d.copy()

        # Remove from the original (will be in the new payload)
        for key in ["type", "binary"]:
            try:
                del d[key]
            except KeyError:
                pass

        # Build the new format
        return (
            {
                "type": copy.get("type"),
                "binary": copy.get("binary"),
                "data": d or None
            }
        )

    type: Optional[str] = None
    """The type of message. This is the message's "official" name provided by TikTok"""

    binary: Optional[bytes] = field(metadata={"serialization_strategy": pass_through}, default=None)
    """Binary of the message if provided. This is useful if there is NO protobuf definition yet"""

    data: Optional[Dict[Any, Any]] = None
    """Data contained within the event. This is useful if the protobuf has been decoded but an event object has not been made."""

    @property
    def base64(self) -> Optional[bytes]:
        """
        Base64 version of message binary *if* binary is provided

        Can be loaded into a decoder such as https://protobuf-decoder.netlify.app/.

        """

        return base64.b64encode(self.binary) if self.binary else None
