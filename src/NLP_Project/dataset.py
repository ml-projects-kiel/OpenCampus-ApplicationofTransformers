import functools
import itertools
import logging
import os
from typing import Optional

import pandas as pd
import tweepy
import yaml
from sklearn.model_selection import train_test_split

from NLP_Project.constants import TWEET_FIELDS, USER_FIELDS, Environment, _logger
from NLP_Project.database import MongoDatabase

RANDOM_SEED = 42


class MissingUserInput(Exception):
    pass


class MissingClient(Exception):
    pass


class DatasetGenerator:
    def __init__(self, environment_vars: Environment, logging_level=logging.INFO) -> None:
        self.tweepy_client = tweepy.Client(
            bearer_token=environment_vars.bearer_token,
            wait_on_rate_limit=True,
            return_type=dict,  # type: ignore
        )
        self.mongo_client = MongoDatabase(
            db_host=environment_vars.db_host,  # type: ignore
            db_port=environment_vars.db_port,  # type: ignore
            db_name=environment_vars.db_name,  # type: ignore
            db_user=environment_vars.db_user,  # type: ignore
            db_password=environment_vars.db_pw,  # type: ignore
            logging_level=logging_level,
        )
        self.logger = functools.partial(_logger, "DatasetGenerator", logging_level)

    def load_userlist(self, userdictpath: str) -> tuple[str, dict[str, list[str]]]:
        userdict_name = os.path.basename(userdictpath).split(".")[0]
        with open(userdictpath, "r") as stream:
            userdict = yaml.safe_load(stream)
        return userdict_name, userdict

    def get_user_timeline(
        self, username: Optional[str] = None, userid: Optional[str] = None, max_results: int = 3200
    ) -> list:
        userdata = self.get_userdata(username, userid)
        return self.__get_user_timeline(userdata["username"], userdata["id"], max_results)

    def get_userdata(self, username: Optional[str], userid: Optional[str]) -> dict:
        if username is None and userid is None:
            raise MissingUserInput("Please provide a valid username or userid")
        return self._get_userdata(username, userid)

    def save_user_timeline(self, username: str, usertweets: list):
        self.mongo_client.save_in_mongodb(username=username, usertweets=usertweets)

    def get_and_save_timeline(
        self, username: str, userid: Optional[str] = None, max_results: int = 3200
    ):
        user_tweets = self.get_user_timeline(
            username=username, userid=userid, max_results=max_results
        )
        if len(user_tweets) == 0:
            return
        self.save_user_timeline(username=username, usertweets=user_tweets)

    def __get_user_timeline(self, username: str, userid: str, max_results: int) -> list:
        expansions = "referenced_tweets.id"

        self.logger("")
        self.logger(f"Downloading user timeline for '{username}'...")
        # Get latest Tweet in MongoDB
        latest_tweet_date = self.mongo_client.get_latest_tweet(username=username)
        if latest_tweet_date is not None:
            self.logger(f"Downloading tweets newer than {latest_tweet_date}...")
        else:
            self.logger(f"No tweets found in mongodb for '{username}'. downloading all tweets...")

        full_results = tweepy.Paginator(
            self.tweepy_client.get_users_tweets,
            id=userid,
            start_time=latest_tweet_date,
            tweet_fields=TWEET_FIELDS,
            expansions=expansions,
        ).flatten(limit=max_results)

        results = [tweet for tweet in full_results]
        self.logger(f"Downloaded {len(results)} tweets for '{username}'.")

        return results

    def _get_userdata(self, username: Optional[str], userid: Optional[str]) -> dict:
        try:
            return self.tweepy_client.get_user(
                username=username, id=userid, user_fields=USER_FIELDS  # type: ignore
            )["data"]
        except tweepy.NotFound as error:
            if userid is None:
                self.logger(f"User '{username}' not found!", ow_level=logging.WARNING)
            elif username is None:
                self.logger(f"User with id '{userid}' not found!", ow_level=logging.WARNING)
            else:
                self.logger(
                    f"User '{username}' with id '{userid}' not found!", ow_level=logging.WARNING
                )
            raise error

    def combine_tweets_to_df(
        self, userlist: list[str], threshold: Optional[int] = None
    ) -> pd.DataFrame:
        data = []
        for idx, user in enumerate(userlist):
            data_raw = self.mongo_client.load_raw_data(user, projection={"_id": 1, "text": 1})
            data_user = [data["text"] for data in data_raw]
            if threshold is not None and len(data_user) < threshold:
                continue
            df = pd.DataFrame({"text": data_user, "label": itertools.repeat(user, len(data_user))})
            df.index = df.index + (idx * 10**6)  # Avoid duplicate indices
            data.append(df)
        return pd.concat(data)

    def create_HF_dataset_rawdata(
        self,
        lang: str,
        df: Optional[pd.DataFrame] = None,
        userlist: Optional[list[str]] = None,
        threshold: Optional[int] = None,
        filename: str = "tweetyface",
    ) -> None:
        if df is None and userlist is None:
            raise MissingUserInput("Please provide a valid DataFrame or list with usernames")
        elif df is None and userlist is not None:
            df = self.combine_tweets_to_df(userlist=userlist, threshold=threshold)
        elif df is not None and userlist is not None:
            raise Warning("Both DataFrame and list with usernames provided. Using DataFrame.")
        else:
            df = df

        df.index.names = ["idx"]  # type: ignore
        train, validate = train_test_split(
            df,
            test_size=0.2,
            shuffle=True,
            random_state=RANDOM_SEED,
            stratify=df["label"].to_list(),  # type: ignore
        )

        for split, split_type in zip([train, validate], ["train", "validation"]):
            json_name = f"data/{filename}_{lang}/{split_type}.json"
            os.makedirs(os.path.dirname(json_name), exist_ok=True)
            _df = pd.DataFrame(split).reset_index().rename(columns={"index": "idx"})
            _df[["text", "label", "idx"]].to_json(
                json_name, orient="records", lines=True, index=True
            )
            self.logger(f"Saved {json_name}.")


def main():
    userdictpaths = ["data/tweetyface.yaml", "data/tweetyface_short.yaml"]
    for userdictpath in userdictpaths:
        env = Environment()
        dataset_generator = DatasetGenerator(env)
        userdict_name, userdict = dataset_generator.load_userlist(userdictpath)
        for lang, userlist in userdict.items():
            for user in userlist:
                try:
                    dataset_generator.get_and_save_timeline(username=user)
                except tweepy.NotFound:
                    continue
            dataset_generator.create_HF_dataset_rawdata(
                lang=lang, userlist=userlist, threshold=1000, filename=userdict_name
            )


if __name__ == "__main__":
    main()
