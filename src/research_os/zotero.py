from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
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
