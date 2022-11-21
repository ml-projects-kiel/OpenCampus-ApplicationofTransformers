from itertools import repeat
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from NLP_Project.constants import Environment
from NLP_Project.database import MongoDatabase


def combine_tweets_to_df(userlist: list[str], mongo_client: MongoDatabase) -> pd.DataFrame:
    data = []
    for user in tqdm(userlist):
        data_user = mongo_client.load_raw_data(user, query={"_id": 1, "text": 1})
        data.append(pd.DataFrame({"text": data_user, "label": repeat(user, len(data_user))}))
    return pd.concat(data)


def save_feature_data(path: str, df: pd.DataFrame):
    table = pa.Table.from_pandas(df)
    pq.write_to_dataset(
        table,
        path,
        partition_cols=["label"],
        compression="snappy",
        existing_data_behavior="delete_matching",
    )


def load_feature_data(path: str, user: Optional[str] = None) -> pd.DataFrame:
    if user is None:
        df = pq.ParquetDataset(path, use_legacy_dataset=False).read().to_pandas()
    else:
        df = (
            pq.ParquetDataset(path, use_legacy_dataset=False, filters=[("label", "=", user)])
            .read()
            .to_pandas()
        )
    return df


def main():
    userlistpath = "data/userlist.txt"
    with open(userlistpath, "r") as f:
        userlist = f.read().splitlines()

    feature_path = "data/feature/combine_tweets.parquet"

    env = Environment()
    mongo_client = MongoDatabase(
        db_host=env.db_host,  # type: ignore
        db_port=env.db_port,  # type: ignore
        db_name=env.db_name,  # type: ignore
        db_user=env.db_user,  # type: ignore
        db_password=env.db_pw,  # type: ignore
    )
    # Load raw data
    df = combine_tweets_to_df(userlist, mongo_client)
    print(df.shape)
    save_feature_data(feature_path, df)

    # Load feature data
    df = load_feature_data(feature_path)
    print(df.shape)
    print(df.head())


if __name__ == "__main__":
    main()
