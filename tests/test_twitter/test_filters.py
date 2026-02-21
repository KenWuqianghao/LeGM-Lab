"""Tests for TweetFilter relevance and skip logic."""

from legm.twitter.filters import TweetFilter

NBA_TAKE = "LeBron is the GOAT and nobody can tell me otherwise"
TEAM_TAKE = "The Lakers are going to win the championship this year"
NO_NBA = "I had a great sandwich for lunch today at the office"


class TestIsRelevant:
    """Tests for TweetFilter.is_relevant."""

    def test_relevant_nba_text(self) -> None:
        """NBA keyword tweet should be relevant."""
        assert TweetFilter().is_relevant(NBA_TAKE) is True

    def test_relevant_with_team_name(self) -> None:
        """A tweet mentioning an NBA team should be relevant."""
        assert TweetFilter().is_relevant(TEAM_TAKE) is True

    def test_irrelevant_no_nba_keywords(self) -> None:
        """No NBA keywords should not be relevant."""
        assert TweetFilter().is_relevant(NO_NBA) is False

    def test_too_short(self) -> None:
        """Tweet shorter than min_length is not relevant."""
        assert TweetFilter(min_length=15).is_relevant("NBA cool") is False

    def test_too_long(self) -> None:
        """Tweet longer than max_length is not relevant."""
        f = TweetFilter(max_length=50)
        assert f.is_relevant("LeBron NBA " + "x" * 50) is False

    def test_exact_min_length_boundary(self) -> None:
        """Tweet at exactly min_length with NBA keyword is relevant."""
        assert TweetFilter(min_length=10).is_relevant("NBA is dope") is True


class TestShouldSkip:
    """Tests for TweetFilter.should_skip."""

    def test_skip_retweets(self) -> None:
        """Tweets starting with 'RT ' should be skipped."""
        f = TweetFilter()
        tweet = {"text": "RT @someone: LeBron NBA", "author_id": "1"}
        assert f.should_skip(tweet) is True

    def test_skip_blocked_accounts(self) -> None:
        """Tweets from blocked accounts should be skipped."""
        f = TweetFilter(blocked_accounts={"999"})
        tweet = {"text": NBA_TAKE, "author_id": "999"}
        assert f.should_skip(tweet) is True

    def test_skip_non_nba_text(self) -> None:
        """Tweets without NBA keywords should be skipped."""
        f = TweetFilter()
        tweet = {"text": NO_NBA, "author_id": "1"}
        assert f.should_skip(tweet) is True

    def test_do_not_skip_valid_nba_tweet(self) -> None:
        """Valid NBA tweet from non-blocked account passes."""
        f = TweetFilter()
        tweet = {"text": NBA_TAKE, "author_id": "1"}
        assert f.should_skip(tweet) is False

    def test_skip_link_only_tweet(self) -> None:
        """Link-only tweets should be skipped."""
        f = TweetFilter()
        tweet = {"text": "https://example.com/article", "author_id": "1"}
        assert f.should_skip(tweet) is True
