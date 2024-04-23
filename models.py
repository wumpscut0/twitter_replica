from typing import List
from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    name: str


class ProfileModel(BaseModel):
    id: int
    name: str
    followers: List[UserModel | None]
    following: List[UserModel | None]


class UserProfileModel(BaseModel):
    result: bool
    user: ProfileModel


class TweetCreateModel(BaseModel):
    result: bool
    tweet_id: int


class MediaCreateModel(BaseModel):
    result: bool
    media_id: int


class SuccessModel(BaseModel):
    result: bool


class UserLikeModel(BaseModel):
    user_id: int
    name: str


class TweetModel(BaseModel):
    id: int
    content: str
    attachments: List[int | None]
    author: UserModel
    likes: List[UserLikeModel | None]


class TapeModel(BaseModel):
    result: bool
    tweets: List[TweetModel]
