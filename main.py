import asyncio
import subprocess
from time import sleep

import uvicorn
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())


def docker_startup():
    sleep(10)
    uvicorn.run("routers:app", host="0.0.0.0")


def local_startup():
    uvicorn.run("routers:app")


if __name__ == "__main__":
    # local_startup()
    docker_startup()

