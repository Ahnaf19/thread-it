"""Per-IP rate limiting on abuse-sensitive public endpoints (ADR-0014).

A small, in-process fixed-window counter — no external store, matching the repo's
thin-owned-code ethos. Single Render instance, so an in-memory dict is the whole
backing store; a multi-instance deploy would swap this for Redis (deferred).
"""

import time

from fastapi import HTTPException, Request

from app.config import settings

# Per-minute caps. Login is the brute-force target, so it's the strictest; checkout
# and cart pricing are looser but still bounded against scripted abuse.
WINDOW_SECONDS = 60
LOGIN_PER_MINUTE = 10
CHECKOUT_PER_MINUTE = 20
CART_PER_MINUTE = 60


class RateLimiter:
    """Fixed-window counter keyed by a caller string.

    Each key is bucketed by `floor(now / window)`; a new bucket resets the count.
    Cheap and O(1); the only imprecision is a possible 2x burst straddling a window
    boundary, which is acceptable for blunting abuse (not metering).
    """

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        # key -> (bucket_index, count)
        self._buckets: dict[str, tuple[int, int]] = {}

    def hit(self, key: str, *, limit: int, window: int = WINDOW_SECONDS) -> tuple[bool, int]:
        """Record one request. Returns (allowed, retry_after_seconds)."""
        now = self._clock()
        bucket = int(now // window)
        prev_bucket, count = self._buckets.get(key, (bucket, 0))
        if prev_bucket != bucket:
            count = 0  # window rolled over
        if count >= limit:
            retry_after = int((bucket + 1) * window - now) + 1
            return False, max(retry_after, 1)
        self._buckets[key] = (bucket, count + 1)
        return True, 0

    def reset(self) -> None:
        self._buckets.clear()


# Module-level singleton — the process-wide limiter shared by every request.
limiter = RateLimiter()


def client_ip(request: Request) -> str:
    """The caller's IP. Behind Render's proxy the real client is the first hop of
    X-Forwarded-For; fall back to the socket peer when there's no proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(*, scope: str, limit: int, window: int = WINDOW_SECONDS):
    """Build a dependency that rejects a caller exceeding `limit` requests per
    `window` seconds on `scope`, with 429 + Retry-After."""

    # Async so FastAPI runs it inline on the event loop, not in a threadpool —
    # the synchronous hit() then executes atomically (no cross-thread race on the
    # shared counter dict). There's no await inside, which is the point.
    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        allowed, retry_after = limiter.hit(
            f"{scope}:{client_ip(request)}", limit=limit, window=window
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests — please slow down.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
