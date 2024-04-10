from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import Table, Integer, ForeignKey, Column, String, ARRAY, LargeBinary
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase): ...


subscription = Table(
    "subscription",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("subscription_id", Integer, ForeignKey("user.id"), primary_key=True),
)


follower = Table(
    "follower",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("follower_id", Integer, ForeignKey("user.id"), primary_key=True),
)


class TweetLike(Base):
    __tablename__ = "tweet_like"
    tweet_id = Column(Integer, ForeignKey("tweet.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)


class Tweet(Base):
    class TweetModel(BaseModel):
        tweet_data: str
        tweet_media_ids: Optional[List[int]]

    __tablename__ = "tweet"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    content = Column(String(300))
    attachments = Column(ARRAY(Integer))
    author = relationship("User", uselist=False)
    users_likes = relationship(
        "User", secondary="tweet_like", cascade="delete, save-update, merge"
    )


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="User")
    api_key = Column(String, unique=True, nullable=False)
    subscriptions = relationship(
        "User",
        secondary="subscription",
        primaryjoin=id == subscription.c.subscription_id,
        secondaryjoin=id == subscription.c.user_id,
        cascade="delete, save-update, merge",
    )

    followers = relationship(
        "User",
        secondary=follower,
        primaryjoin=id == follower.c.follower_id,
        secondaryjoin=id == follower.c.user_id,
        cascade="delete, save-update, merge",
    )

    tweets = relationship(
        "Tweet",
        back_populates="author",
        overlaps="author",
        cascade="delete, save-update, merge",
    )


class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    image = Column(LargeBinary, nullable=False)
