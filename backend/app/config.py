"""Application settings, loaded from environment variables.

Secrets live in each platform's env settings (Render for the backend), never in
the repo — see docs/ROADMAP.md. Locally, a backend/.env file (gitignored) is read.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "Thread It API"
    environment: str = "development"

    # A Product is "new" if created within this many days (drives the NEW badge).
    new_window_days: int = 14

    # CORS — comma-separated list of allowed frontend origins.
    # In production this is the Vercel frontend URL; locally it's the Next.js dev server.
    cors_origins: str = "http://localhost:3000"

    # Database (Supabase Postgres). Unused by the v1 hello-world /health endpoint;
    # wired in when the first models land. Kept here so config has one home.
    database_url: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def database_url_async(self) -> str:
        """`database_url` normalized to the asyncpg driver (see ADR-0002).

        Supabase/Render hand us a plain `postgresql://` string; SQLAlchemy's async
        engine needs the `postgresql+asyncpg://` scheme.
        """
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):  # some providers use the short form
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
