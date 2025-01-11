#!/usr/bin/env python
from dataclasses import dataclass
from datetime import datetime
from os import environ
from time import sleep

import httpx
import stamina


# Tag to use on all Pinboard bookmarks created by this script.
PINBOARD_TAG = "via:pocket"

PINBOARD_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# The Pocket API's rate limit is 320 requests per user per hour,
# which is one request every 11.25 seconds.
# For good measure let's wait at least 24 seconds between Pocket requests
# (including retries and pagination).
# https://getpocket.com/developer/docs/rate-limits
POCKET_RATE_LIMIT = 24

# The Pinboard v1 API's rate limit is one call per user every three seconds.
# The v2 API's rate limit is faster: 400 requests every 15 mins (one every 2.25s).
# For good measure let's wait at least 6 seconds between Pinboard requests
# (including retries).
# https://pinboard.in/api/
# https://pinboard.in/api/v2/overview#rate_limits
PINBOARD_RATE_LIMIT = 6


@dataclass(frozen=True)
class Bookmark:
    url: str
    title: str
    tags: list[str]
    created: datetime


class HTTPClient:
    """HTTP client with rate-limiting and retries."""

    def __init__(self, httpx_client, rate):
        self._httpx_client = httpx_client
        self._last_request: datetime | None = None
        self._rate = rate

    @stamina.retry(on=httpx.HTTPError, timeout=None, wait_initial=10.0, wait_max=300.0)
    def request(self, method, url, params=None, json=None):
        if self._last_request:
            self._wait_at_least(self._rate, self._last_request)

        self._last_request = datetime.now()

        response = self._httpx_client.request(method, url, params=params, json=json)
        return response

    def _wait_at_least(self, seconds: int | float, since: datetime):
        """Wait until at least `seconds` seconds has passed since `since`."""
        sleep(max(5 - (datetime.now() - since).total_seconds(), 0))


class PocketClient:
    def __init__(
        self, http_client: HTTPClient, pocket_consumer_key, pocket_access_token
    ):
        self._http_client = http_client
        self._pocket_consumer_key = pocket_consumer_key
        self._pocket_access_token = pocket_access_token

    def get(self, since):
        """Yield bookmarks from Pocket."""
        count = 30
        offset = 0

        while True:
            json = {
                "consumer_key": self._pocket_consumer_key,
                "access_token": self._pocket_access_token,
                "detailType": "simple",
                "state": "all",
                "sort": "oldest",
                "offset": str(offset),
                "count": str(count),
                "total": "1",
            }

            if since is not None:
                json["since"] = str(int(since.timestamp()))

            response = self._http_client.request(
                "POST", "https://getpocket.com/v3/get", json=json
            )
            response.raise_for_status()

            response_json = response.json()

            for item in response_json["list"].values():
                try:
                    url = item["resolved_url"]
                    title = item["resolved_title"]
                    timestamp = item["time_added"]
                except KeyError:
                    continue

                tags = {PINBOARD_TAG, *item.get("tags", {}).keys()}

                yield Bookmark(url, title, tags, datetime.fromtimestamp(int(timestamp)))

            offset += count
            total = int(response_json["total"])

            if total <= offset:
                return


class PinboardClient:
    def __init__(self, http_client: HTTPClient, pinboard_auth_token):
        self._http_client = http_client
        self._pinboard_auth_token = pinboard_auth_token

    def get(self) -> Bookmark | None:
        """Return the last bookmark that was synced from Pocket to this Pinboard account."""
        response = self._http_client.request(
            "GET",
            "https://api.pinboard.in/v1/posts/all",
            params={
                "format": "json",
                "auth_token": self._pinboard_auth_token,
                "tag": PINBOARD_TAG,
                "results": 1,
            },
        )

        try:
            bookmark_dict = response.json()[0]
        except IndexError:
            return None

        return Bookmark(
            url=bookmark_dict.get("href", ""),
            title=bookmark_dict.get("description", ""),
            tags=bookmark_dict.get("tags", "").split(","),
            created=datetime.strptime(bookmark_dict["time"], PINBOARD_TIME_FORMAT),
        )

    def post(self, bookmark: Bookmark):
        params = {
            "format": "json",
            "auth_token": self._pinboard_auth_token,
            "url": bookmark.url,
            "description": bookmark.title,
            "tags": ",".join([tag.replace(" ", "_") for tag in bookmark.tags]),
            "shared": "no",
            "replace": "no",
            "dt": bookmark.created.strftime(PINBOARD_TIME_FORMAT),
        }

        response = self._http_client.request(
            "GET", "https://api.pinboard.in/v1/posts/add", params=params
        )
        response.raise_for_status()


def main():
    with httpx.Client() as httpx_client:
        pocket_client = PocketClient(
            HTTPClient(httpx_client, POCKET_RATE_LIMIT),
            environ["POCKET_CONSUMER_KEY"],
            environ["POCKET_ACCESS_TOKEN"],
        )
        pinboard_client = PinboardClient(
            HTTPClient(httpx_client, PINBOARD_RATE_LIMIT),
            environ["PINBOARD_AUTH_TOKEN"],
        )

        if last_imported_bookmark := pinboard_client.get():
            since = last_imported_bookmark.created
        else:
            since = None

        for bookmark in pocket_client.get(since):
            print(bookmark)
            pinboard_client.post(bookmark)


if __name__ == "__main__":
    main()
