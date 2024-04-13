from typing import List
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


class Profile(BaseModel):
    id: int
    name: str
    followers: List[User | None]
    following: List[User | None]


class UserProfile(BaseModel):
    result: bool
    user: Profile


class TweetCreate(BaseModel):
    result: bool
    tweet_id: int


class MediaCreate(BaseModel):
    result: bool
    media_id: int


class Success(BaseModel):
    result: bool


class UserLike(BaseModel):
    user_id: int
    name: str


class Tweet(BaseModel):
    id: int
    content: str
    attachments: List[int | None]
    author: User
    likes: List[UserLike | None]


class Tape(BaseModel):
    result: bool
    tweets: List[Tweet]
