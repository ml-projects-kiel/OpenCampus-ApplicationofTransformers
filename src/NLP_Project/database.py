import datetime
import logging
from typing import Optional

import pymongo as pm
from tqdm import tqdm


class MongoDatabase:
    def __init__(
        self,
        db_name: str,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        connection_string: Optional[str] = None,
    ):
        if connection_string is None:
            connection_string = f"mongodb://{db_user}:{db_password}@{db_host}:{db_port}"
        self.client = pm.MongoClient(connection_string)
        self.database = self.client[db_name]

    def load_collection(self, collection_name: str):
        self.collection = self.database[collection_name]

    def save_in_mongodb(self, username: str, usertweets: list) -> None:
        logging.info(f"Saving new tweets for '{username}' in MongoDB...")
        self.load_collection(username)
        update_list = [
            pm.ReplaceOne({"_id": tweet.pop("id")}, tweet, upsert=True)
            for tweet in tqdm(usertweets)
        ]
        self.collection.bulk_write(update_list)

    def load_raw_data(self, collection: str, query: dict) -> list:
        self.load_collection(collection)
        return [data["text"] for data in self.collection.find(projection=query)]

    def get_latest_tweet(self, username: str) -> str | None:
        self.load_collection(username)
        try:
            latest_tweet = [
                tweet for tweet in self.collection.find().sort("created_at", -1).limit(1)
            ][0]
            return self._format_date(latest_tweet["created_at"][:-5])
        except IndexError:
            return None

    def _format_date(self, date: str) -> str:
        datetime_date = datetime.datetime.fromisoformat(date)
        new_latest_date = datetime_date + datetime.timedelta(seconds=1)
        return new_latest_date.isoformat() + "Z"


def main():
    return ()


if __name__ == "__main__":
    main()
