import logging
from itertools import repeat
from typing import Optional

import pandas as pd
import tweepy
import yaml
from datasets.arrow_dataset import Dataset
from tqdm import tqdm

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


def combine_tweets_to_df(
    userlist: list[str], mongo_client: MongoDatabase, threshold: Optional[int] = None
) -> pd.DataFrame:
    data = []
    for user in tqdm(userlist):
        data_user = mongo_client.load_raw_data(user, query={"_id": 1, "text": 1})
        if threshold is not None and len(data_user) < threshold:
            continue
        data.append(pd.DataFrame({"text": data_user, "label": repeat(user, len(data_user))}))
    return pd.concat(data)


def create_HF_dataset(df: pd.DataFrame, dataset_name: str, token: str) -> None:
    df.index.names = ["Date"]

    # Huggingface Dataset
    dataset = Dataset.from_pandas(df)
    dataset = dataset.class_encode_column("label")
    dataset.push_to_hub(dataset_name, token=token, private=True)


def main():
    logging.info("Starting...")
    userdictpath = "data/userlist.yaml"
    with open(userdictpath, "r") as stream:
        userdict = yaml.safe_load(stream)

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
    new_entries = 0
    for user in [entry for dlist in userdict.values() for entry in dlist]:
        try:
            user_data = get_user_data(tweepy_client, user)
        except tweepy.BadRequest:
            logging.info(f"User '{user}' not found. Skipping...")
            continue
        user_tweets = get_user_timeline(
            tweepy_client, mongo_client, username=user, userid=user_data["id"]
        )
        if len(user_tweets) > 0:
            mongo_client.save_in_mongodb(username=user, usertweets=user_tweets)
            new_entries += len(user_tweets)

    if new_entries == 0:
        logging.info("No new entries found. Exiting...")
        return
    print("\n-----------------------------------------------------------")
    print(f"Create new HF dataset with {new_entries} new entries? (y/n)")
    create_new_dataset = input()
    if create_new_dataset == "y":
        for lang, userlist in userdict.items():
            df = combine_tweets_to_df(userlist, mongo_client, threshold=1000)
            logging.info(f"Creating HF dataset for {lang}...")
            create_HF_dataset(
                df, f"ML-Projects-Kiel/tweetyface_{lang}", env.hf_api_token  # type: ignore
            )


if __name__ == "__main__":
    main()
