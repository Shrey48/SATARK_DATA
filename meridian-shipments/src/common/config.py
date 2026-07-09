"""Environment-driven configuration."""
import os


class Config:
    def __init__(self) -> None:
        self.notification_queue_url = os.environ.get("NOTIFICATION_QUEUE_URL", "")
        self.environment = os.environ.get("DEPLOY_ENV", "production")

    def is_production(self) -> bool:
        return self.environment == "production"
