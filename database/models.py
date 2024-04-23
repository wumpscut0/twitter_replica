from typing import List
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

tweet_like = Table(
    "tweet_like",
    Base.metadata,
    Column('tweet_id', Integer, ForeignKey("tweet.id"), primary_key=True),
    Column('user_id', Integer, ForeignKey("user.id"), primary_key=True)
)


class Tweet(Base):
    class TweetSchema(BaseModel):
        tweet_data: str
        tweet_media_ids: List[int | None]

    __tablename__ = "tweet"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(300))
    attachments = Column(ARRAY(Integer))

    author = relationship(
        "User",
        uselist=False,
        back_populates='tweets'
    )
    users_likes = relationship(
        "User",
        secondary="tweet_like",
        back_populates='likes',
    )


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String, default="User")
    api_key = Column(String, unique=True, nullable=False)
    subscriptions = relationship(
        "User",
        secondary="subscription",
        primaryjoin=id == subscription.c.subscription_id,
        secondaryjoin=id == subscription.c.user_id,
    )

    followers = relationship(
        "User",
        secondary=follower,
        primaryjoin=id == follower.c.follower_id,
        secondaryjoin=id == follower.c.user_id,
    )

    tweets = relationship(
        "Tweet",
        back_populates="author",
        cascade='delete, save-update, merge'
    )
    likes = relationship(
        'Tweet',
        secondary='tweet_like',
        back_populates='users_likes',
        cascade="delete, save-update, merge",
    )


class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    image = Column(LargeBinary, nullable=False)
