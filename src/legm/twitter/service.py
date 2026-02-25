"""Twitter API service wrapping tweepy v2 with async support."""

import asyncio
import io
import logging
from typing import Any

import tweepy

logger = logging.getLogger(__name__)


class TwitterService:
    """Async wrapper around tweepy's v2 Client and v1.1 API.

    All tweepy calls are dispatched to a thread via ``asyncio.to_thread``
    since the tweepy library is synchronous.
    """

    def __init__(
        self,
        bearer_token: str,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        self._client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )

        # v1.1 API — needed for media uploads
        auth = tweepy.OAuth1UserHandler(
            api_key,
            api_secret,
            access_token,
            access_token_secret,
        )
        self._api = tweepy.API(auth)

        logger.info("TwitterService initialized")

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------

    async def post_tweet(self, text: str) -> str:
        """Post a tweet and return the tweet ID.

        Args:
            text: Tweet body text (max 280 characters).

        Returns:
            The ID of the created tweet as a string.
        """
        response = await asyncio.to_thread(self._client.create_tweet, text=text)
        tweet_id = str(response.data["id"])
        logger.info("Posted tweet %s", tweet_id)
        return tweet_id

    async def reply_to_tweet(self, text: str, in_reply_to_tweet_id: str) -> str:
        """Reply to an existing tweet.

        Args:
            text: Reply body text.
            in_reply_to_tweet_id: The tweet ID to reply to.

        Returns:
            The ID of the reply tweet as a string.
        """
        response = await asyncio.to_thread(
            self._client.create_tweet,
            text=text,
            in_reply_to_tweet_id=in_reply_to_tweet_id,
        )
        tweet_id = str(response.data["id"])
        logger.info("Replied with tweet %s to %s", tweet_id, in_reply_to_tweet_id)
        return tweet_id

    async def quote_tweet(self, text: str, quoted_tweet_url: str) -> str:
        """Post a quote tweet.

        Args:
            text: Commentary text to accompany the quote.
            quoted_tweet_url: Full URL of the tweet being quoted.  The tweet
                ID is extracted automatically.

        Returns:
            The ID of the quote tweet as a string.
        """
        # Extract tweet ID from URL (last numeric segment)
        quoted_tweet_id = quoted_tweet_url.rstrip("/").split("/")[-1]
        response = await asyncio.to_thread(
            self._client.create_tweet,
            text=text,
            quote_tweet_id=quoted_tweet_id,
        )
        tweet_id = str(response.data["id"])
        logger.info("Quote-tweeted %s with tweet %s", quoted_tweet_id, tweet_id)
        return tweet_id

    async def post_tweet_with_media(
        self,
        text: str,
        image_bytes: bytes,
        *,
        in_reply_to_tweet_id: str | None = None,
        quote_tweet_id: str | None = None,
    ) -> str:
        """Post a tweet with an image attachment.

        Uses the v1.1 media upload endpoint, then attaches the media ID
        to a v2 create_tweet call.

        Args:
            text: Tweet body text (max 280 characters).
            image_bytes: PNG image bytes to attach.
            in_reply_to_tweet_id: Optional tweet ID to reply to.
            quote_tweet_id: Optional tweet ID to quote.

        Returns:
            The ID of the created tweet as a string.
        """
        # Upload media via v1.1 API (requires OAuth 1.0a)
        media = await asyncio.to_thread(
            self._api.media_upload,
            filename="chart.png",
            file=io.BytesIO(image_bytes),
        )

        kwargs: dict[str, Any] = {
            "text": text,
            "media_ids": [media.media_id],
        }
        if in_reply_to_tweet_id:
            kwargs["in_reply_to_tweet_id"] = in_reply_to_tweet_id
        if quote_tweet_id:
            kwargs["quote_tweet_id"] = quote_tweet_id

        response = await asyncio.to_thread(self._client.create_tweet, **kwargs)
        tweet_id = str(response.data["id"])
        logger.info("Posted tweet %s with media %s", tweet_id, media.media_id)
        return tweet_id

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    async def search_recent_tweets(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Search recent tweets matching a query.

        Args:
            query: Twitter search query string.
            max_results: Maximum number of results (10-100).

        Returns:
            List of dicts with keys: id, text, author_id, created_at.
        """
        response = await asyncio.to_thread(
            self._client.search_recent_tweets,
            query=query,
            max_results=max_results,
            tweet_fields=["author_id", "created_at"],
        )

        if not response.data:
            logger.debug("No results for query: %s", query)
            return []

        tweets = [
            {
                "id": str(tweet.id),
                "text": tweet.text,
                "author_id": str(tweet.author_id),
                "created_at": tweet.created_at.isoformat()
                if tweet.created_at
                else None,
            }
            for tweet in response.data
        ]
        logger.info("Found %d tweets for query: %s", len(tweets), query)
        return tweets

    async def get_conversation_thread(
        self,
        tweet_id: str,
        *,
        max_parents: int = 5,
    ) -> list[str]:
        """Walk up the reply chain from a tweet and return texts in chronological order.

        Follows ``referenced_tweets`` of type ``replied_to`` until the root
        tweet is reached or *max_parents* tweets have been collected.

        Args:
            tweet_id: The starting tweet ID (typically the mention).
            max_parents: Maximum number of parent tweets to fetch.

        Returns:
            List of tweet texts ordered root-first (chronological).  The
            starting tweet is **not** included in the returned list.
        """
        thread_texts: list[str] = []
        current_id = tweet_id
        tweet_fields = [
            "conversation_id",
            "referenced_tweets",
            "author_id",
            "created_at",
        ]

        for _ in range(max_parents):
            response = await asyncio.to_thread(
                self._client.get_tweet,
                current_id,
                tweet_fields=tweet_fields,
            )

            if not response.data:
                logger.debug("No data returned for tweet %s", current_id)
                break

            tweet = response.data

            # Find the "replied_to" reference
            parent_id: str | None = None
            if tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "replied_to":
                        parent_id = str(ref.id)
                        break

            if parent_id is None:
                # Reached root of the conversation (or an original tweet)
                break

            # Fetch the parent tweet text
            parent_response = await asyncio.to_thread(
                self._client.get_tweet,
                parent_id,
                tweet_fields=tweet_fields,
            )

            if not parent_response.data:
                logger.debug("Could not fetch parent tweet %s", parent_id)
                break

            thread_texts.append(parent_response.data.text)
            current_id = parent_id

        # Reverse so root tweet comes first (chronological order)
        thread_texts.reverse()
        logger.info(
            "Fetched %d parent tweets for thread starting at %s",
            len(thread_texts),
            tweet_id,
        )
        return thread_texts

    async def get_mentions(
        self,
        user_id: str,
        since_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get mentions of the bot user.

        Args:
            user_id: The bot's Twitter user ID.
            since_id: Only return mentions newer than this tweet ID.

        Returns:
            List of dicts with keys: id, text, author_id, created_at.
        """
        kwargs: dict[str, Any] = {
            "id": user_id,
            "tweet_fields": [
                "author_id",
                "created_at",
                "in_reply_to_user_id",
                "entities",
                "referenced_tweets",
            ],
            "max_results": 100,
        }
        if since_id is not None:
            kwargs["since_id"] = since_id

        response = await asyncio.to_thread(
            self._client.get_users_mentions,
            **kwargs,
        )

        if not response.data:
            logger.debug("No new mentions since %s", since_id)
            return []

        mentions = []
        for tweet in response.data:
            # Extract entities.mentions for position analysis
            entities_mentions: list[dict[str, Any]] = []
            if hasattr(tweet, "entities") and tweet.entities:
                for m in tweet.entities.get("mentions", []):
                    entities_mentions.append(
                        {
                            "start": m["start"],
                            "end": m["end"],
                            "username": m["username"],
                        }
                    )

            # Check if this tweet is a reply
            is_reply = False
            if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets:
                is_reply = any(
                    ref.type == "replied_to" for ref in tweet.referenced_tweets
                )

            mentions.append(
                {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "author_id": str(tweet.author_id),
                    "in_reply_to_user_id": str(tweet.in_reply_to_user_id)
                    if tweet.in_reply_to_user_id
                    else None,
                    "created_at": tweet.created_at.isoformat()
                    if tweet.created_at
                    else None,
                    "is_reply": is_reply,
                    "entities_mentions": entities_mentions,
                }
            )
        logger.info("Found %d new mentions", len(mentions))
        return mentions
