from backend.app.core.config import settings

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:
    sentry_sdk = None
    FastApiIntegration = None


def setup_monitoring() -> None:
    if not settings.sentry_dsn or sentry_sdk is None or FastApiIntegration is None:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.2,
    )
