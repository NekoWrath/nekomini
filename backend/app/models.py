import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), default="")
    last_name = Column(String(255), nullable=True)
    photo_url = Column(String(1024), nullable=True)
    role = Column(String(50), default="viewer")  # viewer, moderator, admin
    
    # Notification preferences
    notify_stream_start = Column(Boolean, default=True)
    notify_announcements = Column(Boolean, default=True)
    notify_answers = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    suggestions = relationship("Suggestion", back_populates="author", cascade="all, delete-orphan")
    votes = relationship("SuggestionVote", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("StreamReminder", back_populates="user", cascade="all, delete-orphan")


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    game_category = Column(String(128), default="Just Chatting")
    platform = Column(String(64), default="Twitch")  # Twitch, Kick, VK Video, YouTube
    platform_url = Column(String(1024), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    is_live = Column(Boolean, default=False, index=True)
    status = Column(String(32), default="scheduled")  # scheduled, live, completed, cancelled
    preview_image_url = Column(String(1024), nullable=True)
    tags = Column(String(255), default="chill,games,giveaway")  # Comma separated
    viewers_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reminders = relationship("StreamReminder", back_populates="stream", cascade="all, delete-orphan")


class StreamReminder(Base):
    __tablename__ = "stream_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True)
    stream_id = Column(Integer, ForeignKey("streams.id", ondelete="CASCADE"), index=True)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reminders")
    stream = relationship("Stream", back_populates="reminders")

    __table_args__ = (
        UniqueConstraint("telegram_id", "stream_id", name="uq_user_stream_reminder"),
    )


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True)
    author_name = Column(String(255), default="Аноним")
    author_username = Column(String(255), nullable=True)
    author_avatar = Column(String(1024), nullable=True)
    
    category = Column(String(64), default="other")  # game_idea, question, challenge, other
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True, default="")
    media_url = Column(String(1024), nullable=True)
    
    upvotes_count = Column(Integer, default=0, index=True)
    status = Column(String(32), default="pending", index=True)  # pending, accepted, rejected, answered
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    author = relationship("User", back_populates="suggestions")
    votes = relationship("SuggestionVote", back_populates="suggestion", cascade="all, delete-orphan")


class SuggestionVote(Base):
    __tablename__ = "suggestion_votes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True)
    suggestion_id = Column(Integer, ForeignKey("suggestions.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="votes")
    suggestion = relationship("Suggestion", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("telegram_id", "suggestion_id", name="uq_user_suggestion_vote"),
    )


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(1024), nullable=True)
    button_text = Column(String(128), nullable=True)
    button_url = Column(String(1024), nullable=True)
    sent_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class StreamerProfile(Base):
    __tablename__ = "streamer_profile"

    id = Column(Integer, primary_key=True, default=1)
    name = Column(String(255), default="StreamerLegend")
    avatar = Column(String(1024), default="https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80")
    bio = Column(Text, default="")
    
    twitch_url = Column(String(1024), nullable=True)
    telegram_channel = Column(String(1024), nullable=True)
    youtube_url = Column(String(1024), nullable=True)
    kick_url = Column(String(1024), nullable=True)
    vk_url = Column(String(1024), nullable=True)
    discord_url = Column(String(1024), nullable=True)
    
    # Donation platform (DonateX)
    donation_url = Column(String(1024), nullable=True)
    donation_title = Column(String(255), default="Поддержать на DonateX")
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
