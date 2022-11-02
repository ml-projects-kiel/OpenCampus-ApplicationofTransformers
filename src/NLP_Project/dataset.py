import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import pymongo as pm
import tweepy
from dotenv import find_dotenv, load_dotenv

logging.basicConfig(level=logging.INFO)


@dataclass(frozen=True)
class Environment:
    logging.info("Loading environment variables.")
    envfile = find_dotenv()
    if not envfile:
        raise FileNotFoundError("No .env file found!")
    logging.info("Found .env file.")
    load_dotenv(envfile)
    access_token: Optional[str] = os.environ.get("ACCESS_TOKEN")
    access_token_secret: Optional[str] = os.environ.get("ACCESS_TOKEN_SECRET")
    bearer_token: Optional[str] = os.environ.get("BEARER_TOKEN")
    client_id: Optional[str] = os.environ.get("CLIENT_ID")
    client_secret: Optional[str] = os.environ.get("CLIENT_SECRET")
    consumer_key: Optional[str] = os.environ.get("CONSUMER_KEY")
    consumer_secret: Optional[str] = os.environ.get("CONSUMER_SECRET")

    db_host: Optional[str] = os.environ.get("DB_HOST")
    db_port: Optional[str] = os.environ.get("DB_PORT")
    db_name: Optional[str] = os.environ.get("DB_NAME")
    db_user: Optional[str] = os.environ.get("DB_USER")
    db_pw: Optional[str] = os.environ.get("DB_PW")


# Download Twitter User Timeline using tweepy
def get_user_timeline(username: str | list, max_results: int = 3200) -> dict[str, list]:
    if isinstance(username, str):
        username = [username]
    env = Environment()
    client = tweepy.Client(bearer_token=env.bearer_token, wait_on_rate_limit=True, return_type=dict)
    tweet_fields = [
        "id",
        "text",
        "edit_history_tweet_ids",
        "edit_controls",
        "attachments",
        "author_id",
        "context_annotations",
        "conversation_id",
        "created_at",
        "entities",
        "geo",
        "in_reply_to_user_id",
        "lang",
        # "non_public_metrics",
        "public_metrics",
        # "organic_metrics",
        # "promoted_metrics",
        "possibly_sensitive",
        "referenced_tweets",
        "reply_settings",
        "source",
        "withheld",
    ]
    expansions = "referenced_tweets.id"

    results = dict()
    logging.info("Downloading user timeline...")
    for user in username:
        logging.info(f"Downloading user timeline for '{user}'...")
        try:
            user_data = get_user_data(user)
        except tweepy.BadRequest:
            continue
        results[user] = dict()
        results[user]["user_data"] = user_data
        temp = tweepy.Paginator(
            client.get_users_tweets,
            id=user_data["id"],
            tweet_fields=tweet_fields,
            expansions=expansions,
        ).flatten(limit=max_results)

        results[user]["tweets"] = [tweet for tweet in temp]

    return results


def get_user_data(username: str) -> dict:
    env = Environment()
    client = tweepy.Client(bearer_token=env.bearer_token, wait_on_rate_limit=True, return_type=dict)
    user_fields = [
        "id",
        "name",
        "username",
        "created_at",
        "description",
        "entities",
        "location",
        "protected",
        "public_metrics",
        "verified",
    ]
    try:
        return client.get_user(username=username, user_fields=user_fields)["data"]
    except tweepy.BadRequest as error:
        logging.error(f"User '{username}' not found!")
        raise error


# Save dictionary to json file
def save_json(data: dict, path: str) -> None:
    os.makedirs(path, exist_ok=True)
    logging.info("Saving json file...")
    for user in data.keys():
        if os.path.isfile(f"{path}/{user}.json"):
            logging.info(f"Found old data for '{user}'. Extending data...")
            with open(f"{path}/{user}.json", "r") as f:
                old_data = json.load(f)
            new_data = extend_tweet_data(old_data, data[user])
        else:
            new_data = data[user]
        with open(f"{path}/{user}.json", "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4)


def extend_tweet_data(olddata: dict, newdata: dict) -> dict:
    old_ids = [tweet["id"] for tweet in olddata["tweets"]]
    new_tweets = [tweet for tweet in newdata["tweets"] if tweet["id"] not in old_ids]
    logging.info(f"Found {len(new_tweets)} new tweets.")
    return {"user_data": newdata["user_data"], "tweets": olddata["tweets"] + new_tweets}


def connectmongodb() -> pm.MongoClient:
    env = Environment()
    mongodb_url = f"mongodb://{env.db_user}:{env.db_pw}@{env.db_host}:{env.db_port}"
    client = pm.MongoClient(mongodb_url)
    return client[env.db_name]


def load_collection(collection_name: str) -> pm.collection.Collection:
    client = connectmongodb()
    return client[collection_name]


def save_in_mongodb(data: dict) -> None:
    logging.info("Saving data in MongoDB...")
    for user in data.keys():
        logging.info(f"Saving new tweets for '{user}' in MongoDB...")
        collection = load_collection(user)
        tweet_list = data[user]["tweets"]
        for tweet in tweet_list:
            tweet["_id"] = tweet.pop("id")
            collection.replace_one({"_id": tweet["_id"]}, tweet, upsert=True)


def main():
    userlist = ["@sdfs", "elonmusk", "neiltyson", "BillGates"]

    results = get_user_timeline(userlist)
    save_json(results, "data/raw")
    save_in_mongodb(results)


if __name__ == "__main__":
    main()
