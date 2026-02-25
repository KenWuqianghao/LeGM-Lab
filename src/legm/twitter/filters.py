"""Tweet filtering logic for NBA relevance and spam detection."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class TweetFilter:
    """Filters tweets for NBA relevance and quality.

    Applies length bounds, keyword matching, and blocked-account checks
    to decide whether the bot should engage with a tweet.
    """

    NBA_KEYWORDS: set[str] = {
        # League
        "nba",
        "basketball",
        "hoops",
        "playoffs",
        "finals",
        "all-star",
        "all star",
        "triple double",
        "double double",
        "free throw",
        "three pointer",
        "dunk",
        "buzzer beater",
        "draft",
        # Slang / opinion keywords
        "washed",
        "goat",
        "mvp",
        "dpoy",
        "6moy",
        "roty",
        "clutch",
        "carried",
        "choke",
        "ring",
        "ringz",
        "bus rider",
        "bus driver",
        "supermax",
        "trade",
        "cooked",
        "fraud",
        # Teams
        "celtics",
        "nets",
        "knicks",
        "76ers",
        "sixers",
        "raptors",
        "bulls",
        "cavaliers",
        "cavs",
        "pistons",
        "pacers",
        "bucks",
        "hawks",
        "hornets",
        "heat",
        "magic",
        "wizards",
        "nuggets",
        "timberwolves",
        "wolves",
        "thunder",
        "trail blazers",
        "blazers",
        "jazz",
        "warriors",
        "clippers",
        "lakers",
        "suns",
        "kings",
        "mavericks",
        "mavs",
        "rockets",
        "grizzlies",
        "pelicans",
        "spurs",
        # Notable players (last names)
        "lebron",
        "james",
        "curry",
        "steph",
        "durant",
        "giannis",
        "antetokounmpo",
        "jokic",
        "luka",
        "doncic",
        "tatum",
        "embiid",
        "morant",
        "booker",
        "edwards",
        "wemby",
        "wembanyama",
        "brunson",
        "haliburton",
        "shai",
        "gilgeous-alexander",
        "davis",
        "kawhi",
        "leonard",
        "lillard",
        "mitchell",
        "towns",
        "bam",
        "adebayo",
        "ingram",
        "zion",
        "williamson",
        "fox",
        "maxey",
    }

    def __init__(
        self,
        min_length: int = 15,
        max_length: int = 300,
        blocked_accounts: set[str] | None = None,
    ) -> None:
        self._min_length = min_length
        self._max_length = max_length
        self._blocked_accounts: set[str] = blocked_accounts or set()

    def is_relevant(self, tweet_text: str) -> bool:
        """Check if a tweet is NBA-relevant based on length and keywords.

        Args:
            tweet_text: The full text of the tweet.

        Returns:
            True if the tweet passes length bounds and contains at least
            one NBA keyword.
        """
        text_len = len(tweet_text)
        if text_len < self._min_length or text_len > self._max_length:
            return False

        text_lower = tweet_text.lower()
        return any(keyword in text_lower for keyword in self.NBA_KEYWORDS)

    def should_skip(
        self, tweet: dict[str, Any], *, is_mention: bool = False
    ) -> bool:
        """Determine whether the bot should skip this tweet.

        Args:
            tweet: A dict with at least ``text`` and ``author_id`` keys.
            is_mention: If True, skip the NBA-keyword and length checks
                since the user explicitly @'d the bot.

        Returns:
            True if the tweet should be skipped (i.e., not engaged with).
        """
        text: str = tweet.get("text", "")
        author_id: str = str(tweet.get("author_id", ""))

        # Skip retweets
        if text.startswith("RT "):
            logger.debug("Skipping retweet: %s", text[:60])
            return True

        # Skip link-only tweets (just URLs, maybe with whitespace)
        stripped = re.sub(r"https?://\S+", "", text).strip()
        if not stripped:
            logger.debug("Skipping link-only tweet: %s", text[:60])
            return True

        # Skip blocked accounts
        if author_id in self._blocked_accounts:
            logger.debug("Skipping blocked author %s", author_id)
            return True

        # For direct mentions, skip relevance check — they asked for it
        if is_mention:
            return False

        # Skip if not NBA-relevant
        if not self.is_relevant(text):
            logger.debug("Skipping irrelevant tweet: %s", text[:60])
            return True

        return False
