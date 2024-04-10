import requests
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from unittest import TestCase


class TestTwitterReplica(TestCase):
    BASE_URL = "http://localhost:8000"
    headers = {"api-key": "pytest"}
    user_id = None
    other_user_id_for_follow = None
    other_user_id_for_unfollow = None
    image_id = None
    tweet_id_for_delete = None
    tweet_id_for_like = None
    tweet_id_for_unlike = None

    @classmethod
    def setUpClass(cls):
        cls.user_id = requests.get(
            cls.BASE_URL + "/api/users/me", headers=cls.headers
        ).json()["user"]["id"]
        cls.other_user_id_for_follow = requests.get(
            cls.BASE_URL + "/api/users/me", headers={"api-key": "other_1"}
        ).json()["user"]["id"]
        cls.other_user_id_for_unfollow = requests.get(
            cls.BASE_URL + "/api/users/me", headers={"api-key": "other_2"}
        ).json()["user"]["id"]
        requests.post(
            cls.BASE_URL + f"/api/users/{cls.other_user_id_for_unfollow}/follow",
            headers=cls.headers,
        )

        with open("33584.jpg", "rb") as file:
            cls.image_id = requests.post(
                cls.BASE_URL + "/api/medias", files={"file": file.read()}
            ).json()["media_id"]

        tweet_with_image = {"tweet_data": "Hello", "tweet_media_ids": [cls.image_id]}
        tweet = {"tweet_data": "Hello", "tweet_media_ids": []}
        cls.tweet_id_for_like = requests.post(
            cls.BASE_URL + "/api/tweets", headers=cls.headers, json=tweet_with_image
        ).json()["tweet_id"]
        cls.tweet_id_for_unlike = requests.post(
            cls.BASE_URL + "/api/tweets", headers=cls.headers, json=tweet
        ).json()["tweet_id"]
        cls.tweet_id_for_delete = requests.post(
            cls.BASE_URL + "/api/tweets", headers=cls.headers, json=tweet
        ).json()["tweet_id"]
        requests.post(
            cls.BASE_URL + f"/api/tweets/{cls.tweet_id_for_unlike}/likes",
            headers=cls.headers,
        )

    def test_get_tweets(self):
        r = requests.get(self.BASE_URL + "/api/tweets", headers=self.headers)
        assert r.status_code == 200

    def test_get_image(self):
        r = requests.get(self.BASE_URL + f"/{self.image_id}", headers=self.headers)
        assert r.status_code == 200

    def test_get_self_profile(self):
        r = requests.get(self.BASE_URL + "/api/users/me", headers=self.headers)
        assert r.status_code == 200

    def test_add_tweet(self):
        tweet_data = "Hello"
        tweet_media_ids = [self.image_id]

        tweet_dict = {"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids}
        r = requests.post(
            self.BASE_URL + "/api/tweets", headers=self.headers, json=tweet_dict
        )
        assert r.status_code == 201

    def test_delete_tweet(self):
        r = requests.delete(
            self.BASE_URL + f"/api/tweets/{self.tweet_id_for_delete}",
            headers=self.headers,
        )
        assert r.status_code == 200

    def test_like(self):
        r = requests.post(
            self.BASE_URL + f"/api/tweets/{self.tweet_id_for_like}/likes",
            headers=self.headers,
        )
        assert r.status_code == 201

    def test_unlike(self):
        r = requests.delete(
            self.BASE_URL + f"/api/tweets/{self.tweet_id_for_unlike}/likes",
            headers=self.headers,
        )
        assert r.status_code == 200

    def test_load_image(self):
        with open("33584.jpg", "rb") as file:
            r = requests.post(
                self.BASE_URL + "/api/medias", files={"file": file.read()}
            )
        assert r.status_code == 201

    def test_get_any_profile(self):
        r = requests.get(self.BASE_URL + f"/api/users/{self.other_user_id_for_follow}")
        assert r.status_code == 200

    def test_follow(self):
        r = requests.post(
            self.BASE_URL + f"/api/users/{self.other_user_id_for_follow}/follow",
            headers=self.headers,
        )
        assert r.status_code == 201

    def test_unfollow(self):
        r = requests.delete(
            self.BASE_URL + f"/api/users/{self.other_user_id_for_unfollow}/follow",
            headers=self.headers,
        )
        assert r.status_code == 200
