"""HTTP client with Chrome TLS impersonation (the anti-block trick).

Uses curl_cffi so requests look like a real browser at the TLS handshake
level, not just the User-Agent string. Each call rotates the impersonated
Chrome version.
"""

import random

from curl_cffi.requests import AsyncSession

CHROME_VERSIONS = [
    "chrome110",
    "chrome116",
    "chrome119",
    "chrome120",
    "chrome123",
    "chrome124",
    "chrome131",
    "chrome133a",
]

BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def random_impersonate() -> str:
    """Pick a random Chrome fingerprint for this request."""
    return random.choice(CHROME_VERSIONS)


async def fetch(
    url: str,
    *,
    method: str = "GET",
    params: dict | None = None,
    data: dict | None = None,
    headers: dict | None = None,
    cookies: dict | None = None,
    timeout: int = 12,
    proxy: str | None = None,
    session: AsyncSession | None = None,
) -> str:
    """Fetch a URL behind Chrome impersonation. Returns response text."""
    base = {"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        base.update(headers)

    kw = dict(
        params=params,
        data=data,
        headers=base,
        cookies=cookies,
        timeout=timeout,
        impersonate=random_impersonate(),
        proxy=proxy,
    )
    if session is not None:
        resp = await session.request(method, url, **kw)
        resp.raise_for_status()
        return resp.text
    async with AsyncSession() as s:
        resp = await s.request(method, url, **kw)
        resp.raise_for_status()
        return resp.text
