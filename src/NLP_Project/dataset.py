import datetime
import json
import logging
import os

import pymongo as pm
import tweepy
from tqdm import tqdm

from NLP_Project.constants import TWEET_FIELDS, USER_FIELDS, Environment

logging.basicConfig(level=logging.INFO)


# Download Twitter User Timeline using tweepy
def get_user_timeline(
    client: tweepy.Client, username: str, userid: str, max_results: int = 3200
) -> list:
    expansions = "referenced_tweets.id"

    logging.info(f"Downloading user timeline for '{username}'...")
    # Get latest Tweet in MongoDB
    try:
        latest_tweet = get_lastest_tweet_from_mongo(username)
        latest_tweet_date = datetime.datetime.fromisoformat(latest_tweet["created_at"][:-5])
        new_latest_date = latest_tweet_date + datetime.timedelta(seconds=1)
        latest_tweet_date = new_latest_date.isoformat() + "Z"
        logging.info(f"Downloading tweets newer than {latest_tweet_date}...")
    except IndexError:
        logging.info(f"No tweets found in MongoDB for '{username}'. Downloading all tweets...")
        latest_tweet_date = None

    temp = tweepy.Paginator(
        client.get_users_tweets,
        id=userid,
        start_time=latest_tweet_date,
        tweet_fields=TWEET_FIELDS,
        expansions=expansions,
    ).flatten(limit=max_results)

    results = [tweet for tweet in temp]
    logging.info(f"Downloaded {len(results)} tweets for '{username}'.")

    return results


def get_user_data(client: tweepy.Client, username: str) -> dict:
    try:
        return client.get_user(username=username, user_fields=USER_FIELDS)["data"]
    except tweepy.BadRequest as error:
        logging.error(f"User '{username}' not found!")
        raise error


# Save dictionary to json file
def save_json(username: str, userdata: dict, usertweets: list, path: str) -> None:
    os.makedirs(path, exist_ok=True)
    logging.info("Saving json file...")
    if os.path.isfile(f"{path}/{username}.json"):
        logging.info(f"Found old data for '{username}'. Extending data...")
        with open(f"{path}/{username}.json", "r") as f:
            old_data = json.load(f)
        new_tweets = extend_tweet_data(old_data["tweets"], usertweets)
    else:
        new_tweets = usertweets
    data = {"user": userdata, "tweets": new_tweets}
    with open(f"{path}/{username}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def extend_tweet_data(oldtweets: list, newtweets: list) -> list:
    old_ids = [tweet["id"] for tweet in oldtweets]
    new_tweets = [tweet for tweet in newtweets if tweet["id"] not in old_ids]
    logging.info(f"Found {len(new_tweets)} new tweets.")
    return oldtweets + new_tweets


def connectmongodb() -> pm.MongoClient:
    env = Environment()
    mongodb_url = f"mongodb://{env.db_user}:{env.db_pw}@{env.db_host}:{env.db_port}"
    client = pm.MongoClient(mongodb_url)
    return client[env.db_name]


def load_collection(collection_name: str) -> pm.collection.Collection:
    client = connectmongodb()
    return client[collection_name]


def save_in_mongodb(username: str, usertweets: list) -> None:
    logging.info(f"Saving new tweets for '{username}' in MongoDB...")
    collection = load_collection(username)
    for tweet in tqdm(usertweets):
        tweet["_id"] = tweet.pop("id")
        collection.replace_one({"_id": tweet["_id"]}, tweet, upsert=True)


def get_lastest_tweet_from_mongo(username: str) -> dict:
    collection = load_collection(username)
    try:
        return [tweet for tweet in collection.find().sort("created_at", -1).limit(1)][0]
    except IndexError:
        raise IndexError(f"No tweets found for '{username}' in MongoDB!")


def main():
    logging.info("Starting...")
    userlist = ["MKBHD", "@sdfs", "elonmusk", "neiltyson", "BillGates"]

    env = Environment()
    client = tweepy.Client(bearer_token=env.bearer_token, wait_on_rate_limit=True, return_type=dict)
    for user in userlist:
        try:
            user_data = get_user_data(client, user)
        except tweepy.BadRequest:
            logging.info(f"User '{user}' not found. Skipping...")
            continue
        user_tweets = get_user_timeline(client, username=user, userid=user_data["id"])
        if len(user_tweets) > 0:
            save_json(username=user, userdata=user_data, usertweets=user_tweets, path="data/raw")
            save_in_mongodb(username=user, usertweets=user_tweets)


if __name__ == "__main__":
    main()
