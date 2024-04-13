from contextlib import asynccontextmanager
from aiofiles import tempfile
from sqlalchemy.exc import IntegrityError

from database.engine import create_all, session_factory
from database.queries import (
    add_user,
    load_tweet,
    load_image,
    get_image,
    delete_tweet,
    like,
    unlike,
    get_user_profile_by_id,
    follow,
    unfollow,
    get_tape, get_user_profile_by_api_key,
)
from database.models import Tweet

import logging
from fastapi import FastAPI, Request, Header
from starlette.staticfiles import FileResponse, StaticFiles
from starlette.responses import JSONResponse

from models import User, TweetCreate, MediaCreate, Success, Tape, UserProfile


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    yield


app = FastAPI(lifespan=lifespan)

exception_collector = logging.getLogger("exception_collector")

app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")


@app.get('/')
async def home():
    return FileResponse('static/index.html')


@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')


@app.get("/{media_id}")
async def get_image_(media_id: int):
    async with session_factory() as session:
        image = await get_image(session, media_id)
    async with tempfile.NamedTemporaryFile(delete=False) as file:
        await file.write(image.image)
    return FileResponse(file.name, media_type="image/png")


@app.get("/api/users/me", response_model=UserProfile)
async def get_user_profile(api_key=Header()):
    try:
        async with session_factory() as session:
            await add_user(session, api_key)
    except IntegrityError:
        pass

    async with session_factory() as session:
        profile = await get_user_profile_by_api_key(session, api_key)
        return profile


@app.post("/api/tweets", response_model=TweetCreate)
async def load_tweet_(tweet: Tweet.TweetModel, api_key=Header()):
    async with session_factory() as session:
        tweet_id = await load_tweet(session, api_key, tweet)
    return JSONResponse({"result": True, "tweet_id": tweet_id}, 201)


@app.delete("/api/tweets/{id}", response_model=Success)
async def delete_tweet_(id: int, api_key=Header(...)):
    async with session_factory() as session:
        if await delete_tweet(session, id, api_key):
            return {"result": True}
        else:
            return JSONResponse(
                {
                    "result": False,
                    "error_type": "ValidationException",
                    "error_message": "Cannot delete someone else's tweet",
                },
                409,
            )


@app.post("/api/tweets/{id}/likes", response_model=Success, status_code=201)
async def like_(id: int, api_key=Header(...)):
    async with session_factory() as session:
        await like(session, id, api_key)
        return {'result': "true"}


@app.delete("/api/tweets/{id}/likes", response_model=Success)
async def unlike_(id: int, api_key=Header(...)):
    async with session_factory() as session:
        await unlike(session, id, api_key)
        return {"result": True}


@app.post("/api/medias", response_model=MediaCreate, status_code=201)
async def load_image_(request: Request):
    image = (await request.form()).get("file")
    async with session_factory() as session:
        image_id = await load_image(session, await image.read())
    return {"result": True, "media_id": image_id}


@app.get("/api/tweets", response_model=Tape)
async def get_tweets(api_key=Header()):
    try:
        async with session_factory() as session:
            await add_user(session, api_key)
    except IntegrityError:
        pass
    async with session_factory() as session:
        tape = await get_tape(session, api_key)
        return tape


@app.get("/api/users/{id}", response_model=UserProfile)
async def get_other_profile(id: int):
    async with session_factory() as session:
        return await get_user_profile_by_id(session, id)


@app.post("/api/users/{id}/follow", response_model=Success, status_code=201)
async def follow_(id: int, api_key=Header()):
    async with session_factory() as session:
        await follow(session, id, api_key)
        return {'result': True}


@app.delete("/api/users/{id}/follow", response_model=Success)
async def unfollow_(id: int, api_key=Header()):
    async with session_factory() as session:
        await unfollow(session, id, api_key)
        return {"result": True}


@app.middleware("http")
async def internal_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"{type(e)}\n{e}\n{e.args}\n\n")
        return JSONResponse(
            {
                "result": False,
                "error_type": "Internal server error",
                "error_message": e.__repr__(),
            },
            500,
        )
