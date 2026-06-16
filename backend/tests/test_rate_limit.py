"""Per-IP rate limiting (ADR-0014): the limiter algorithm + the endpoint wiring."""

from app.rate_limit import LOGIN_PER_MINUTE, RateLimiter

WRONG_LOGIN = {"username": "owner", "password": "wrong"}


# ---- unit: the fixed-window counter, with an injected clock (no real sleeps) ----

def test_allows_up_to_limit_then_blocks():
    rl = RateLimiter(clock=lambda: 0.0)
    results = [rl.hit("login:1.2.3.4", limit=3, window=60)[0] for _ in range(4)]
    assert results == [True, True, True, False]


def test_window_rollover_resets_count():
    now = {"t": 0.0}
    rl = RateLimiter(clock=lambda: now["t"])
    for _ in range(3):
        rl.hit("login:1.2.3.4", limit=3, window=60)
    assert rl.hit("login:1.2.3.4", limit=3, window=60)[0] is False
    now["t"] = 60.0  # next window
    assert rl.hit("login:1.2.3.4", limit=3, window=60)[0] is True


def test_blocked_hit_reports_retry_after():
    rl = RateLimiter(clock=lambda: 10.0)
    rl.hit("k", limit=1, window=60)
    allowed, retry_after = rl.hit("k", limit=1, window=60)
    assert allowed is False
    assert 1 <= retry_after <= 60


def test_keys_are_independent():
    rl = RateLimiter(clock=lambda: 0.0)
    rl.hit("login:1.1.1.1", limit=1, window=60)
    # A different IP (different key) is unaffected by the first's exhausted budget.
    assert rl.hit("login:2.2.2.2", limit=1, window=60)[0] is True


# ---- integration: the /admin/login endpoint enforces the cap and returns 429 ----

async def test_login_over_limit_returns_429(client, admin_password):
    # Wrong creds still count (the limiter runs as a dependency, before the handler).
    for _ in range(LOGIN_PER_MINUTE):
        resp = await client.post("/admin/login", json=WRONG_LOGIN)
        assert resp.status_code == 401
    blocked = await client.post("/admin/login", json=WRONG_LOGIN)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


async def test_distinct_ips_have_independent_budgets(client, admin_password):
    other_ip = {"X-Forwarded-For": "203.0.113.9"}
    for _ in range(LOGIN_PER_MINUTE):
        await client.post("/admin/login", json=WRONG_LOGIN, headers=other_ip)
    # The default-IP caller is untouched by the forwarded IP exhausting its budget.
    resp = await client.post("/admin/login", json=WRONG_LOGIN)
    assert resp.status_code == 401
