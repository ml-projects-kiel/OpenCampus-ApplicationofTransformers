from itertools import repeat
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from NLP_Project.dataset import load_collection


def load_raw_data(user: str):
    collection = load_collection(user)
    return [data["text"] for data in collection.find(projection={"_id": 1, "text": 1})]


def combine_tweets_to_df(userlist: list[str]) -> pd.DataFrame:
    data = []
    for user in tqdm(userlist):
        data_user = load_raw_data(user)
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


def load_feature_data(path: str, user: Optional[str] = None):
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

    # Load raw data
    df = combine_tweets_to_df(userlist)
    print(df.shape)
    save_feature_data(feature_path, df)

    # Load feature data
    df = load_feature_data(feature_path)
    print(df.shape)
    print(df.head())


if __name__ == "__main__":
    main()
