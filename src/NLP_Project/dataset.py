import json
import logging
import os

import tweepy

from NLP_Project.constants import TWEET_FIELDS, USER_FIELDS, Environment
from NLP_Project.database import MongoDatabase

logging.basicConfig(level=logging.INFO)


# Download Twitter User Timeline using tweepy
def get_user_timeline(
    tweepy_client: tweepy.Client,
    mongo_client: MongoDatabase,
    username: str,
    userid: str,
    max_results: int = 3200,
) -> list:
    expansions = "referenced_tweets.id"

    logging.info(f"Downloading user timeline for '{username}'...")
    # Get latest Tweet in MongoDB
    latest_tweet_date = mongo_client.get_latest_tweet(username=username)
    if latest_tweet_date is not None:
        logging.info(f"Downloading tweets newer than {latest_tweet_date}...")
    else:
        logging.info(f"No tweets found in mongodb for '{username}'. downloading all tweets...")

    temp = tweepy.Paginator(
        tweepy_client.get_users_tweets,
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
        return client.get_user(username=username, user_fields=USER_FIELDS)["data"]  # type: ignore
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


def main():
    logging.info("Starting...")
    userlistpath = "data/userlist.txt"
    with open(userlistpath, "r") as f:
        userlist = f.read().splitlines()

    env = Environment()
    tweepy_client = tweepy.Client(
        bearer_token=env.bearer_token, wait_on_rate_limit=True, return_type=dict  # type: ignore
    )
    mongo_client = MongoDatabase(
        db_host=env.db_host,  # type: ignore
        db_port=env.db_port,  # type: ignore
        db_name=env.db_name,  # type: ignore
        db_user=env.db_user,  # type: ignore
        db_password=env.db_pw,  # type: ignore
    )
    for user in userlist:
        try:
            user_data = get_user_data(tweepy_client, user)
        except tweepy.BadRequest:
            logging.info(f"User '{user}' not found. Skipping...")
            continue
        user_tweets = get_user_timeline(
            tweepy_client, mongo_client, username=user, userid=user_data["id"]
        )
        if len(user_tweets) > 0:
            save_json(username=user, userdata=user_data, usertweets=user_tweets, path="data/raw")
            mongo_client.save_in_mongodb(username=user, usertweets=user_tweets)


if __name__ == "__main__":
    main()
