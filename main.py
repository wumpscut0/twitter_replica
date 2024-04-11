import logging
import subprocess
from time import sleep

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())


def build_exception_collector():
    exc_assembler = logging.getLogger("exception_collector")
    exc_assembler.setLevel(logging.INFO)
    handler = logging.FileHandler("unhandled_exceptions.txt")
    handler.setFormatter(logging.Formatter("%(message)s"))
    exc_assembler.addHandler(handler)


def docker_startup():
    sleep(10)
    subprocess.run("uvicorn routers:app --host 0.0.0.0", shell=True)


def local_startup():
    build_exception_collector()
    subprocess.run("uvicorn routers:app", shell=True)


if __name__ == "__main__":
    # local_startup()
    docker_startup()

