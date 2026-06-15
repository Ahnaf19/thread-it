"""Application settings, loaded from environment variables.

Secrets live in each platform's env settings (Render for the backend), never in
the repo — see docs/ROADMAP.md. Locally, a backend/.env file (gitignored) is read.
"""

from urllib.parse import quote

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
        engine needs the `postgresql+asyncpg://` scheme. We also percent-encode the
        password so connection strings whose password contains URL-reserved chars
        (`@`, `%`, `?`, …) parse correctly — the raw Supabase string works as-is.
        """
        url = self.database_url
        if not url:
            return url

        # Normalize the scheme to asyncpg.
        for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
            if url.startswith(prefix):
                rest = url[len(prefix):]
                break
        else:
            return url  # unrecognized scheme — leave untouched

        # Split user-info from host on the LAST '@'. The host never contains '@',
        # so this correctly isolates the boundary even when the password does.
        if "@" not in rest:
            return f"postgresql+asyncpg://{rest}"
        userinfo, host = rest.rsplit("@", 1)
        if ":" in userinfo:
            user, password = userinfo.split(":", 1)
            userinfo = f"{user}:{quote(password, safe='')}"
        return f"postgresql+asyncpg://{userinfo}@{host}"


settings = Settings()
