import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import find_dotenv, load_dotenv

logging.basicConfig(level=logging.INFO)

TWEET_FIELDS = [
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

USER_FIELDS = [
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


def main():
    return ()


if __name__ == "__main__":
    main()
