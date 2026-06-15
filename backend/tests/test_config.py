from app.config import Settings


def test_async_url_encodes_password_with_special_chars():
    s = Settings(database_url="postgresql://postgres.ref:p@ss%w?rd@aws-1.pooler.supabase.com:5432/postgres")
    # @ % ? in the password are percent-encoded; host (split on last @) is intact.
    assert s.database_url_async == (
        "postgresql+asyncpg://postgres.ref:p%40ss%25w%3Frd@aws-1.pooler.supabase.com:5432/postgres"
    )


def test_async_url_normalizes_scheme():
    s = Settings(database_url="postgresql://user:simple@host:5432/db")
    assert s.database_url_async.startswith("postgresql+asyncpg://")


def test_async_url_empty_stays_empty():
    assert Settings(database_url="").database_url_async == ""


def test_async_url_strips_trailing_newline():
    # A pasted env value often carries a trailing newline; it must not leak into
    # the database name.
    s = Settings(database_url="postgresql://user:pw@host:5432/postgres\n")
    assert s.database_url_async == "postgresql+asyncpg://user:pw@host:5432/postgres"
