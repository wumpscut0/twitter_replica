import pytest
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from fastapi.testclient import TestClient
from routers import app


@pytest.fixture(scope='session')
def client():
    with TestClient(app, headers={'api-key': 'test'}) as client_:
        yield client_


@pytest.fixture(scope="session")
def image_id(client):
    with open("33584.jpg", "rb") as file:
        yield client.post("/api/medias", files={'file': file}).json()['media_id']


@pytest.fixture(scope='session')
def other_user_id(client):
    yield client.get("/api/users/me", headers={'api-key': 'test2'}).json()['user']['id']


@pytest.fixture(scope="session")
def tweet_id(client, image_id):
    tweet = {
        "tweet_data": 'hello',
        "tweet_media_ids": [image_id],
    }
    yield client.post("/api/tweets", json=tweet).json()['tweet_id']


########################################################################################################################


@pytest.mark.asyncio
@pytest.mark.parametrize('route', ("/api/users/me", "/api/tweets"))
async def test_200(route, client):
    response = client.get(route)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_image(client, image_id):
    response = client.get(f"/{image_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_load_tweet_with_image(client, image_id):
    tweet_data = {
        "tweet_data": "hello",
        "tweet_media_ids": [image_id],
    }
    response = client.post("/api/tweets", json=tweet_data)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_like(client, tweet_id):
    response = client.post(f"/api/tweets/{tweet_id}/likes")
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_unlike(client, tweet_id):
    response = client.delete(f"/api/tweets/{tweet_id}/likes")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_tweet(client, tweet_id):
    response = client.delete(f"/api/tweets/{tweet_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_load_image(client):
    with open("33584.jpg", "rb") as file:
        response = client.post(f"/api/medias", files={"file": file})
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_other_user_profile(client, other_user_id):
    response = client.get(f"/api/users/{other_user_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_follow(client, other_user_id):
    response = client.post(f"/api/users/{other_user_id}/follow")
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_unfollow(client, other_user_id):
    response = client.delete(f"/api/users/{other_user_id}/follow")
    assert response.status_code == 200
