from typing import Literal

from fastapi import Request
from shared.constants import PROXY_COUNT, PROXY_HEADERS
from shared.types.schemas import RequestInfo


def get_client_ip(
    request: Request,
    proxy_headers: list[str] | None = None,
    trusted_proxies: list[str] | None = None,
    proxy_count: int | None = None,
) -> str | None:
    """
    Extract the client IP address using a variety of methods.
    """

    proxy_headers = proxy_headers or PROXY_HEADERS
    proxy_count = proxy_count or PROXY_COUNT

    for header_name in proxy_headers:
        if header_name in request.headers:
            header_value = request.headers[header_name]

            if header_name == "X-Forwarded-For" and "," in header_value:
                ips = [ip.strip() for ip in header_value.split(",")]

                if trusted_proxies:
                    if ips[-1] in trusted_proxies:
                        idx = -1 - proxy_count
                        if abs(idx) <= len(ips):
                            return ips[idx]
                else:
                    return ips[0]
            else:
                return header_value

    if hasattr(request, "client") and request.client and hasattr(request.client, "host"):
        return request.client.host

    return None


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "Unknown")


def get_request_info(
    request: Request,
    keys: list[Literal["user_agent", "ip_address", "request_id", "cookies", "authorization"]] = [  # noqa: B006
        "user_agent",
        "ip_address",
        "request_id",
        "cookies",
        "authorization",
    ],
) -> RequestInfo:
    """
    Extract specified information from the request object.

    Args:
        request (Request): The FastAPI request object.
        keys (list[Literal["user_agent", "ip_address", "request_id", "cookies", "authorization"]]): List of keys to extract. Supported keys are 'user_agent', 'ip_address', 'request_id', 'cookies', and 'authorization'.

    Returns:
        RequestInfo: A RequestInfo object containing the extracted information.
    """

    info = RequestInfo()

    if "user_agent" in keys:
        user_agent = get_user_agent(request)
        info.user_agent = user_agent

    if "request_id" in keys:
        request_id: str | None = (
            request.state.request_id if hasattr(request.state, "request_id") else request.headers.get("X-Request-ID")
        )
        info.request_id = request_id or "Unknown"

    if "ip_address" in keys:
        ip_address = get_client_ip(request)
        info.ip_address = ip_address or "Unknown"

    if "cookies" in keys:
        info.cookies = dict(request.cookies) or {}

    if "authorization" in keys:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                info.authorization = parts[1]
            else:
                info.authorization = auth_header
        else:
            info.authorization = None

    return info
