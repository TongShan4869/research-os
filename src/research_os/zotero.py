from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


LOCAL_API_URL = "http://127.0.0.1:23119/"


@dataclass(frozen=True)
class ZoteroStatus:
    available: bool
    message: str


def check_zotero(timeout: float = 0.25) -> ZoteroStatus:
    try:
        with urlopen(LOCAL_API_URL, timeout=timeout):
            pass
    except HTTPError as error:
        if error.code < 500:
            return ZoteroStatus(True, "Zotero local API is reachable.")
        return ZoteroStatus(False, f"Zotero local API returned HTTP {error.code}.")
    except (TimeoutError, URLError, OSError) as error:
        return ZoteroStatus(False, f"Zotero local API unavailable at {LOCAL_API_URL}: {error}")
    return ZoteroStatus(True, "Zotero local API is reachable.")


class ZoteroLocalClient:
    def __init__(self, base_url: str = LOCAL_API_URL, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def collections(self) -> list[dict[str, Any]]:
        collections = self._get_json("/api/users/0/collections?format=json&limit=1000")
        return [collection.get("data", collection) for collection in collections]

    def collection_top_items(self, collection_key: str) -> list[dict[str, Any]]:
        quoted_key = quote(collection_key, safe="")
        return self._get_json(f"/api/users/0/collections/{quoted_key}/items/top?format=json&limit=1000")

    def _get_json(self, path: str) -> list[dict[str, Any]]:
        with urlopen(f"{self.base_url}{path}", timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Zotero local API returned non-list response for {path}")
        return data
