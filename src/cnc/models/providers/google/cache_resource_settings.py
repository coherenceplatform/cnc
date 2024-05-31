from typing import Literal
from cnc.models.config.resource import CacheResourceSettings
from cnc.logger import get_logger

log = get_logger(__name__)


class GCPCacheResourceSettings(CacheResourceSettings):
    provider: Literal["gcp"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def provider_version(self):
        _version = float(self.version)
        if _version == 7.2:
            return "REDIS_7_2"

        major_version = int(_version)
        if major_version == 6:
            return "REDIS_6_X"

        return "REDIS_{{ service.settings.version }}_0"

    @property
    def toolbox_ssh_port_mapping(self):
        return f"{self.local_port}:{self.redis_ip}:{self.redis_port}"
