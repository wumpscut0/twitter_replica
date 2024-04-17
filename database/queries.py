from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from database.models import User, Tweet, Image


async def build_user_as_api_format(user: User):
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


async def build_tweet_as_api_format(session: AsyncSession, tweet: Tweet):
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


async def get_user_by_api_key(session: AsyncSession, api_key: str):
    return (
        await session.execute(select(User).where(User.api_key == api_key))
    ).scalar()


async def get_user_by_id(session: AsyncSession, user_id: str):
    return await session.get(User, ident=user_id)


async def get_user_profile_by_api_key(session: AsyncSession, api_key: str):
    query = (
        select(User)
        .options(selectinload(User.subscriptions), selectinload(User.followers))
        .filter(User.api_key == api_key)
    )

    user = (await session.execute(query)).scalar()

    return await build_user_as_api_format(user)


async def get_user_profile_by_id(session: AsyncSession, user_id: int):
    query = (
        select(User)
        .options(selectinload(User.subscriptions), selectinload(User.followers))
        .filter(User.id == user_id)
    )
    user = (await session.execute(query)).scalar()

    return await build_user_as_api_format(user)


async def add_user(session: AsyncSession, api_key: str):
    user = User(api_key=api_key)
    session.add(user)
    await session.commit()
    return user.id


# async def get_tape(session: AsyncSession, api_key: str):
#     users = []
#     user_subscriptions = []
#     tweets = []
#     user = (
#         await session.execute(
#             select(User)
#             .where(User.api_key == api_key)
#             .options(selectinload(User.tweets), selectinload(User.subscriptions))
#         )
#     ).scalar()
#     users.append(user)
#
#     # vvv sorting subscriptions by popularity vvv
#     for user in user.subscriptions:
#         user = (
#             await session.execute(
#                 select(User)
#                 .where(User.id == user.id)
#                 .options(selectinload(User.followers), selectinload(User.tweets))
#             )
#         ).scalar()
#         user_subscriptions.append((len(user.followers), user))
#     users.extend(
#         [
#             user
#             for quantity_followers, user in sorted(
#                 user_subscriptions, key=lambda subscribe: subscribe[0], reverse=True
#             )
#         ]
#     )
#     # ^^^ vvv sorting subscriptions by popularity ^^^
#
#     for user in users:
#         for tweet in user.tweets:
#             tweets.append(await build_tweet_as_api_format(session, tweet))
#
#     tweets.reverse()
#     result = {"result": True, "tweets": tweets}
#     return result


async def get_tape(session: AsyncSession, api_key: str):
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

    # vvv get subscriptions tweets vvv
    processed_users = []
    for user in users:
        processed_users.append(user.id)
        user_tweets = [await build_tweet_as_api_format(session, tweet) for tweet in user.tweets]
        user_tweets.reverse()
        tweets.extend(user_tweets)
    # ^^^ get subscriptions tweets ^^^

    # vvv get tweets other users vvv
    users = (await session.execute(select(User).filter(~User.id.in_(processed_users)).options(selectinload(User.tweets)))).scalars()
    print(users)
    for user in users:
        user_tweets = [await build_tweet_as_api_format(session, tweet) for tweet in user.tweets]
        user_tweets.reverse()
        tweets.extend(user_tweets)
    # ^^^ vvv get tweets other users ^^^

    result = {"result": True, "tweets": tweets}
    return result


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


async def load_tweet(session: AsyncSession, api_key, tweet):
    content, attachments = tweet.tweet_data, tweet.tweet_media_ids
    user: User = await get_user_by_api_key(session, api_key)
    tweet = Tweet(user_id=user.id, content=content, attachments=attachments)
    session.add(tweet)
    await session.commit()
    return tweet.id


async def load_image(session: AsyncSession, image: bytes):
    image = Image(image=image)
    session.add(image)
    await session.commit()
    return image.id


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

# async def delete_user(user_id):
#     async with session_factory.begin() as session:
#         await session.delete(await session.get(User, ident=user_id))
#         session.commit()
