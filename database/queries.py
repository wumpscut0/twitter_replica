from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from database.engine import session_factory
from database.models import User, Tweet, Image


async def build_user_as_api_format(user: User):
    return {
        "result": "true",
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": [
                {"id": follower.id, "name": follower.name}
                for follower in user.followers
            ],
            "following": [
                {
                    "id": subscribe.id,
                    "name": subscribe.name,
                }
                for subscribe in user.subscriptions
            ],
        },
    }


async def get_user_by_api_key(api_key: str):
    async with session_factory() as session:
        return (
            await session.execute(select(User).where(User.api_key == api_key))
        ).scalar()


async def get_user_by_id(user_id: str):
    async with session_factory() as session:
        return await session.get(User, ident=user_id)


async def get_user_profile_by_api_key(api_key: str):
    async with session_factory() as session:
        query = (
            select(User)
            .options(selectinload(User.subscriptions), selectinload(User.followers))
            .filter(User.api_key == api_key)
        )
        user = (await session.execute(query)).scalar()

        return await build_user_as_api_format(user)


async def get_user_profile_by_id(user_id: int):
    async with session_factory() as session:
        query = (
            select(User)
            .options(selectinload(User.subscriptions), selectinload(User.followers))
            .filter(User.id == user_id)
        )
        user = (await session.execute(query)).scalar()

        return await build_user_as_api_format(user)


async def add_user(api_key: str):
    try:
        async with session_factory.begin() as session:
            user = User(api_key=api_key)
            session.add(user)
            return user.id
    except IntegrityError:
        async with session_factory.begin() as session:
            user = (
                await session.execute(select(User).where(User.api_key == api_key))
            ).scalar()
            return user.id


async def get_tape(api_key: str):
    async with session_factory() as session:
        users = []
        user_subscriptions = []
        tweets = []
        user = (
            await session.execute(
                select(User)
                .where(User.api_key == api_key)
                .options(selectinload(User.tweets), selectinload(User.subscriptions))
            )
        ).scalar()
        users.append(user)

        # vvv sorting subscriptions by popularity vvv
        for user in user.subscriptions:
            user = (
                await session.execute(
                    select(User)
                    .where(User.id == user.id)
                    .options(selectinload(User.followers), selectinload(User.tweets))
                )
            ).scalar()
            user_subscriptions.append((len(user.followers), user))
        users.extend(
            [
                user
                for quantity_followers, user in sorted(
                    user_subscriptions, key=lambda subscribe: subscribe[0], reverse=True
                )
            ]
        )
        # ^^^ vvv sorting subscriptions by popularity ^^^

        for user in users:
            for tweet in user.tweets:
                tweets.append(
                    {
                        "id": tweet.id,
                        "content": tweet.content,
                        "attachments": tweet.attachments,
                        "author": {"id": user.id, "name": user.name},
                        "likes": [
                            {"user_id": user.id, "name": user.name}
                            for user in (
                                await session.execute(
                                    select(Tweet)
                                    .where(Tweet.id == tweet.id)
                                    .options(selectinload(Tweet.users_likes))
                                )
                            )
                            .scalar()
                            .users_likes
                        ],
                    }
                )

        result = {"result": True, "tweets": tweets}
        return result


async def like(tweet_id: int, api_key: str):
    async with session_factory() as session:
        user = (
            await session.execute(select(User).where(User.api_key == api_key))
        ).scalar()
        tweet = (await session.execute(select(Tweet).where(Tweet.id == tweet_id).options(selectinload(Tweet.users_likes)))).scalar()
        tweet.users_likes.append(user)
        await session.commit()


async def unlike(tweet_id: int, api_key: str):
    async with session_factory() as session:
        user = (
            await session.execute(select(User).where(User.api_key == api_key))
        ).scalar()
        tweet = (await session.execute(
            select(Tweet).where(Tweet.id == tweet_id).options(selectinload(Tweet.users_likes)))).scalar()
        tweet.users_likes.remove(user)
        await session.commit()


async def delete_tweet(tweet_id: int, api_key: str):
    async with session_factory() as session:
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


async def load_tweet(api_key, content, attachments):
    async with session_factory() as session:
        user: User = await get_user_by_api_key(api_key)
        tweet = Tweet(user_id=user.id, content=content, attachments=attachments)
        session.add(tweet)
        await session.commit()
        return tweet.id


async def load_image(image: bytes):
    async with session_factory() as session:
        image = Image(image=image)
        session.add(image)
        await session.commit()
        return image.id


async def get_image(image_id):
    async with session_factory() as session:
        return await session.get(Image, ident=image_id)


async def follow(user_id: int, api_key: str):
    async with session_factory() as session:
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


async def unfollow(user_id: int, api_key: str):
    async with session_factory() as session:
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


# async def delete_user(user_id):
#     async with session_factory.begin() as session:
#         await session.delete(await session.get(User, ident=user_id))
#         session.commit()

