import re
from typing import Any

from ..exceptions import ValidationError


def validate_url(url: str) -> bool:
    pattern = r"^https?://.+"
    if not re.match(pattern, url):
        raise ValidationError(
            f"Invalid URL: {url}. Must start with http:// or https://", field_name="url"
        )
    return True


def validate_proxy(proxy: str) -> bool:
    if not proxy:
        return False

    ip_port_with_auth = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+:\w+:\w+$"
    ip_port_simple = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
    http_url = r"^https?://.+"

    if (
        re.match(ip_port_with_auth, proxy)
        or re.match(ip_port_simple, proxy)
        or re.match(http_url, proxy)
    ):
        return True

    return False


def validate_headers(headers: dict[str, Any]) -> bool:
    if not isinstance(headers, dict):
        raise ValidationError("Headers must be a dictionary", field_name="headers")

    for key, value in headers.items():
        if not isinstance(key, str):
            raise ValidationError(
                f"Header key must be a string, got {type(key).__name__}", field_name="headers"
            )
        if not isinstance(value, str):
            raise ValidationError(
                f"Header value for key '{key}' must be a string, got {type(value).__name__}",
                field_name="headers",
            )

    return True


def normalize_urls(urls: str | list[str] | None) -> list[str] | None:
    if urls is None:
        return None
    if isinstance(urls, str):
        return [urls]
    return urls
