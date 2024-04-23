from sqlalchemy import select, insert, Result, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models import User, Tweet, Image


class UserApiFormatMixin:
    @staticmethod
    async def _build_user_as_api_format(user: User):
        return {
            "result": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "followers": [
                    {"id": follower.id, "name": follower.name}
                    for follower in user.followers
                ],
                "following": [
                    {"id": subscribe.id, "name": subscribe.name}
                    for subscribe in user.subscriptions
                ],
            }
        }


class TweetApiFormatMixin:
    @staticmethod
    async def _build_tweet_as_api_format(session: AsyncSession, tweet: Tweet):
        tweet = (
            await session.execute(
                select(Tweet)
                .where(Tweet.id == tweet.id)
                .options(selectinload(Tweet.users_likes), selectinload(Tweet.author))
            )
        ).scalar()

        return {
            "id": tweet.id,
            "content": tweet.content,
            "attachments": tweet.attachments,
            "author": {"id": tweet.author.id, "name": tweet.author.name},
            "likes": [{'user_id': user.id, "name": user.name} for user in tweet.users_likes],
        }


class Tape(TweetApiFormatMixin):
    _process_users = []
    _users = []
    _tweets = []

    @classmethod
    async def get_tape(cls, session: AsyncSession, api_key: str):
        owner = await cls._get_owner(session, api_key)
        cls._process_users.append(owner.id)
        await cls._sorting_owner_subscriptions(session, owner)

        tape = await cls._get_tape(session)
        await cls._reset()
        return tape

    @classmethod
    async def _reset(cls):
        cls._process_users = []
        cls._users = []
        cls._tweets = []

    @classmethod
    async def _get_owner(cls, session: AsyncSession, api_key: str):
        user = (
            await session.execute(
                select(User)
                .where(User.api_key == api_key)
                .options(selectinload(User.tweets), selectinload(User.subscriptions))
            )
        ).scalar()
        cls._process_users.append(user.id)
        cls._users.append(user)
        return user

    @classmethod
    async def _sorting_owner_subscriptions(cls, session: AsyncSession, owner: User):
        user_subscriptions = []
        for subscribe in owner.subscriptions:
            cls._process_users.append(subscribe.id)
            subscribe = (
                await session.execute(
                    select(User)
                    .where(User.id == subscribe.id)
                    .options(selectinload(User.followers), selectinload(User.tweets))
                )
            ).scalar()
            user_subscriptions.append((len(subscribe.followers), subscribe))
        cls._users.extend(
            [
                user
                for quantity_followers, user in sorted(
                    user_subscriptions, key=lambda subscribe: subscribe[0], reverse=True
                )
            ]
        )

    @classmethod
    async def _get_tape(cls, session: AsyncSession):
        tweets = []
        cls._users.extend((await session.execute(
            select(User).filter(~User.id.in_(cls._process_users)).options(selectinload(User.tweets)))).scalars())

        for user in cls._users:
            user_tweets = [await cls._build_tweet_as_api_format(session, tweet) for tweet in user.tweets]
            user_tweets.reverse()
            tweets.extend(user_tweets)

        return {"result": True, "tweets": tweets}


class Profile(UserApiFormatMixin):
    @classmethod
    async def get_user_profile_by_api_key(cls, session: AsyncSession, api_key: str):
        query = (
            select(User)
            .options(selectinload(User.subscriptions), selectinload(User.followers))
            .filter(User.api_key == api_key)
        )

        user = (await session.execute(query)).scalar()

        return await cls._build_user_as_api_format(user)

    @classmethod
    async def get_user_profile_by_id(cls, session: AsyncSession, user_id: int):
        query = (
            select(User)
            .options(selectinload(User.subscriptions), selectinload(User.followers))
            .filter(User.id == user_id)
        )
        user = (await session.execute(query)).scalar()

        return await cls._build_user_as_api_format(user)


async def get_user_by_api_key(session: AsyncSession, api_key: str):
    return (
        await session.execute(select(User).where(User.api_key == api_key))
    ).scalar()


async def get_user_by_id(session: AsyncSession, user_id: str):
    return await session.get(User, ident=user_id)


async def add_user(session: AsyncSession, api_key: str):
    await session.execute(insert(User).values(api_key=api_key))
    await session.commit()
    return (await session.execute(select(User).order_by(desc(User.id)).limit(1))).scalar().id


async def like(session: AsyncSession, tweet_id: int, api_key: str):
    user = await get_user_by_api_key(session, api_key)
    tweet = (await session.execute(
        select(Tweet).where(Tweet.id == tweet_id).options(selectinload(Tweet.users_likes)))).scalar()
    tweet.users_likes.append(user)
    await session.commit()


async def unlike(session: AsyncSession, tweet_id: int, api_key: str):
    user = await get_user_by_api_key(session, api_key)
    tweet = (await session.execute(
        select(Tweet).where(Tweet.id == tweet_id).options(selectinload(Tweet.users_likes)))).scalar()
    tweet.users_likes.remove(user)
    await session.commit()


async def delete_tweet(session: AsyncSession, tweet_id: int, api_key: str):
    tweet = (
        await session.execute(
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .options(selectinload(Tweet.author))
        )
    ).scalar()
    if tweet.author.api_key == api_key:
        await session.delete(tweet)
        await session.commit()
        return True
    else:
        return False


async def load_tweet(session: AsyncSession, api_key, tweet) -> int:
    content, attachments = tweet.tweet_data, tweet.tweet_media_ids
    user: User = await get_user_by_api_key(session, api_key)
    await session.execute(insert(Tweet).values(user_id=user.id, content=content, attachments=attachments))
    await session.commit()
    return (await session.execute(select(Tweet).order_by(desc(Tweet.id)).limit(1))).scalar().id


async def load_image(session: AsyncSession, image: bytes):
    await session.execute(insert(Image).values(image=image))
    await session.commit()
    return (await session.execute(select(Image).order_by(desc(Image.id)).limit(1))).scalar().id


async def get_image(session: AsyncSession, image_id):
    return await session.get(Image, ident=image_id)


async def follow(session: AsyncSession, user_id: int, api_key: str):
    subscribe: User = (
        await session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.followers))
        )
    ).scalar()
    follower: User = (
        await session.execute(
            select(User)
            .where(User.api_key == api_key)
            .options(selectinload(User.subscriptions))
        )
    ).scalar()
    follower.subscriptions.append(subscribe)
    subscribe.followers.append(follower)
    await session.commit()


async def unfollow(session: AsyncSession, user_id: int, api_key: str):
    subscribe: User = (
        await session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.followers))
        )
    ).scalar()
    follower: User = (
        await session.execute(
            select(User)
            .where(User.api_key == api_key)
            .options(selectinload(User.subscriptions))
        )
    ).scalar()
    try:
        follower.subscriptions.remove(subscribe)
        subscribe.followers.remove(follower)
    except ValueError:
        return
    await session.commit()
