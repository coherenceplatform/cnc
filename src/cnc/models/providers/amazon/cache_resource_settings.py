from typing import Literal

from cnc.models.config.resource import CacheResourceSettings
from cnc.logger import get_logger

log = get_logger(__name__)


class AWSCacheResourceSettings(CacheResourceSettings):
    provider: Literal["aws"]

    @property
    def toolbox_ssh_port_mapping(self):
        return (
            "{"
            f'"host":["{self.redis_ip}"],"portNumber":["{self.redis_port}"], '
            f'"localPortNumber":["{self.local_port}"]'
            "}"
        )
