import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dotenv import find_dotenv, load_dotenv

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


def _logger(name, level, msg, exc_info=None, ow_level=None):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.basicConfig(
        level=level,
    )
    report_level = logging.INFO if ow_level is None else ow_level
    logging.log(report_level, f"{time_now} | {name:20} | {msg}", exc_info=exc_info)


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

    hf_api_token: Optional[str] = os.environ.get("HUGGINGFACE_API_TOKEN")


def main():
    return ()


if __name__ == "__main__":
    main()
