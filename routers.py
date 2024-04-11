from contextlib import asynccontextmanager
from aiofiles import tempfile
from database.engine import create_all
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
    get_user_profile_by_api_key,
    unfollow,
    get_tape,
)
from database.models import Tweet

import logging
from fastapi import FastAPI, Request, Header
from starlette.staticfiles import FileResponse, StaticFiles
from starlette.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all()
    yield


app = FastAPI(lifespan=lifespan)
exception_collector = logging.getLogger("exception_collector")

app.mount("/css", StaticFiles(directory="static/css"), name="css")

# Монтирование директории для статических файлов JavaScript
app.mount("/js", StaticFiles(directory="static/js"), name="js")


@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')


@app.get("/api/users/me")
async def get_user_profile(api_key=Header()):
    await add_user(api_key)
    return await get_user_profile_by_api_key(api_key)


@app.get("/{media_id}", response_class=FileResponse)
async def get_image_(media_id: int):
    image = await get_image(media_id)
    async with tempfile.NamedTemporaryFile(delete=False) as file:
        await file.write(image.image)
    return FileResponse(file.name, media_type="image/png")


@app.post("/api/tweets")
async def load_tweet_(tweet: Tweet.TweetModel, api_key=Header()):
    tweet_id = await load_tweet(api_key, tweet.tweet_data, tweet.tweet_media_ids)
    return JSONResponse({"result": True, "tweet_id": tweet_id}, 201)


@app.delete("/api/tweets/{id}")
async def delete_tweet_(id: int, api_key=Header(...)):
    if await delete_tweet(id, api_key):
        return {"result": True}
    else:
        return JSONResponse(
            {
                "result": False,
                "error_type": "ValidationException",
                "error_message": "Cannot delete someone else's tweet",
            },
            422,
        )


@app.post("/api/tweets/{id}/likes")
async def like_(id: int, api_key=Header(...)):
    await like(id, api_key)
    return JSONResponse(
        {
            "result": True,
        },
        201,
    )


@app.delete("/api/tweets/{id}/likes")
async def unlike_(id: int, api_key=Header(...)):
    await unlike(id, api_key)
    return {"result": True}


@app.post("/api/medias")
async def load_image_(request: Request):
    image = (await request.form()).get("file")
    image_id = await load_image(await image.read())
    return JSONResponse({"result": True, "media_id": image_id}, 201)


@app.get("/api/tweets")
async def get_tweets(api_key=Header()):
    return await get_tape(api_key)


@app.get("/api/users/{id}")
async def get_other_profile(id: int):
    return await get_user_profile_by_id(id)


@app.post("/api/users/{id}/follow")
async def follow_(id: int, api_key=Header()):
    await follow(id, api_key)
    return JSONResponse(
        {
            "result": True,
        },
        201,
    )


@app.delete("/api/users/{id}/follow")
async def unfollow_(id: int, api_key=Header()):
    await unfollow(id, api_key)
    return {"result": True}


@app.middleware("http")
async def internal_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        exception_collector.info(f"{type(e)}\n{e}\n{e.args}\n\n")
        print(f"{type(e)}\n{e}\n{e.args}\n\n")
        return JSONResponse(
            {
                "result": False,
                "error_type": "Internal server error",
                "error_message": e.__repr__(),
            },
            500,
        )
