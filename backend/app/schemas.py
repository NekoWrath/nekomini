import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

# ==================== User Schemas ====================
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    photo_url: Optional[str] = None

class UserOut(UserBase):
    role: str
    notify_stream_start: bool
    notify_announcements: bool
    notify_answers: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class UserSettingsUpdate(BaseModel):
    notify_stream_start: Optional[bool] = None
    notify_announcements: Optional[bool] = None
    notify_answers: Optional[bool] = None


# ==================== Stream Schemas ====================
class StreamBase(BaseModel):
    title: str
    description: Optional[str] = ""
    game_category: str = "Just Chatting"
    platform: str = "Twitch"
    platform_url: str
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime] = None
    preview_image_url: Optional[str] = None
    tags: Optional[str] = "gaming,chill"

class StreamCreate(StreamBase):
    pass

class StreamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    game_category: Optional[str] = None
    platform: Optional[str] = None
    platform_url: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    preview_image_url: Optional[str] = None
    tags: Optional[str] = None
    is_live: Optional[bool] = None
    status: Optional[str] = None

class StreamOut(StreamBase):
    id: int
    is_live: bool
    status: str
    viewers_count: int
    has_reminder: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Suggestion Schemas ====================
class SuggestionCreate(BaseModel):
    category: str = "other"  # game_idea, question, challenge, other
    title: str
    content: Optional[str] = ""
    media_url: Optional[str] = None

class SuggestionModerate(BaseModel):
    status: str  # accepted, rejected, answered, pending
    admin_reply: Optional[str] = None

class SuggestionOut(BaseModel):
    id: int
    telegram_id: int
    author_name: str
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    category: str
    title: str
    content: Optional[str] = ""
    media_url: Optional[str] = None
    upvotes_count: int
    has_voted: bool = False
    is_author: bool = False
    status: str
    admin_reply: Optional[str] = None
    replied_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Broadcast & Admin ====================
class BroadcastRequest(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None

class BroadcastResponse(BaseModel):
    success: bool
    sent_count: int
    failed_count: int
    message: str

class StreamerProfileOut(BaseModel):
    name: str = "StreamerLegend"
    avatar: str = ""
    bio: Optional[str] = ""
    twitch_url: Optional[str] = None
    telegram_channel: Optional[str] = None
    youtube_url: Optional[str] = None
    kick_url: Optional[str] = None
    vk_url: Optional[str] = None
    discord_url: Optional[str] = None
    donation_url: Optional[str] = None
    donation_title: Optional[str] = "Поддержать на DonateX"

    model_config = ConfigDict(from_attributes=True)

class StreamerProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    twitch_url: Optional[str] = None
    telegram_channel: Optional[str] = None
    youtube_url: Optional[str] = None
    kick_url: Optional[str] = None
    vk_url: Optional[str] = None
    discord_url: Optional[str] = None
    donation_url: Optional[str] = None
    donation_title: Optional[str] = None
