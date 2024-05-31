import re
import hashlib
from typing import (
    List,
    Optional,
    Any,
    Literal,
    Union,
    Annotated,
)
from pydantic import (
    field_validator,
    Field,
    model_validator,
)

from cnc.models.base_model import BaseModel, IgnoredType
from cnc.models.custom_header import CustomHeaders
from cnc.models.providers.amazon import (
    AWSCustomHeaders,
    AWSDeployResourceLimits,
)
from cnc.models.providers.google import GCPDeployResourceLimits
from .utils import validate_command_list
from cnc.utils import clean_name_string

from cnc.logger import get_logger

log = get_logger(__name__)


class ServiceBuildTimeoutsConfig(BaseModel):
    default: Optional[int] = 20
    test: Optional[int] = 20
    migrate: Optional[int] = 20
    snapshot: Optional[int] = 20
    seed: Optional[int] = 20
    deploy: Optional[int] = 20


class ServiceBuildConfig(BaseModel):
    included_paths: Optional[List[str]] = []
    excluded_paths: Optional[List[str]] = []
    existing_image_tag_mode: Optional[Literal["static", "sha"]] = "static"


class PlatformSettings(BaseModel):
    min_scale: Optional[int] = 1
    max_scale: Optional[int] = 4


class SystemSettings(BaseModel):
    health_check: Optional[str] = "/"
    platform_settings: Optional[PlatformSettings] = Field(
        default_factory=PlatformSettings
    )


class CDNSettings(BaseModel):
    enabled: Optional[bool] = True


class GCPCustomHeaders(CustomHeaders):
    provider: Literal["gcp"]


class BaseServiceSettings(BaseModel):
    type: str
    internal: Optional[bool] = False
    data: Optional[dict] = {}
    url_path: Optional[str] = "/"
    custom_headers: Optional[
        Union[
            AWSCustomHeaders,
            GCPCustomHeaders,
        ]
    ] = Field(
        discriminator="provider",
        default=None,
    )
    cdn: Optional[CDNSettings] = Field(default_factory=CDNSettings)
    system: Optional[SystemSettings] = Field(default_factory=SystemSettings)
    build_config: Optional[ServiceBuildConfig] = Field(
        default_factory=ServiceBuildConfig
    )
    timeouts: Optional[ServiceBuildTimeoutsConfig] = Field(
        default_factory=ServiceBuildTimeoutsConfig
    )
    provider: str

    # ------------------------------
    # Parent relationships
    # ------------------------------
    config: Optional[IgnoredType] = IgnoredType()
    service: Optional[IgnoredType] = IgnoredType()

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="before")
    def format_custom_headers(cls, data, info):
        if isinstance(data.get("custom_headers"), list):
            data["custom_headers"] = {
                "headers": data.get("custom_headers", []),
                "provider": info.context.get("provider"),
            }
        return data

    @field_validator("url_path", mode="before")
    def validate_command(cls, value: str) -> str:
        # if empty, default to "/"
        return value.strip().rstrip("/") or "/"

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def is_web(self):
        return False

    @property
    def is_cache(self):
        return False

    @property
    def application(self):
        return self.service.environment.application

    @property
    def is_resource(self):
        return False

    @property
    def unique_id(self):
        _hash = hashlib.sha256()
        _hash.update(
            f"{self.service.environment.application.name}:{self.service.environment.collection.name}:{self.service.environment.name}:{self.service.name}:{self.url_path}:{self.system.health_check}".encode()
        )
        return _hash.hexdigest()

    @property
    def managed_environment_variables(self):
        _data = {
            "CNC_INSTANCE_NAME": self.service.instance_name,
            "PORT": self.service.port,
        }

        if self.service.domain:
            _data["CNC_ENVIRONMENT_DOMAIN"] = self.service.domain

        return _data

    @property
    def custom_request_headers(self):
        headers = []

        if self.custom_headers:
            for header in self.custom_headers.headers:
                if header.header_type == "request":
                    headers.append(header)

        return headers

    @property
    def custom_response_headers(self):
        headers = []

        if self.custom_headers:
            for header in self.custom_headers.headers:
                if header.header_type == "response":
                    headers.append(header)

        return headers

    @property
    def existing_instance_name(self):
        return


class CORSSettings(BaseModel):
    allowed_origins: List[str]


class FrontendCDNConfig(BaseModel):
    enabled: Optional[bool] = False


class BackendCDNConfig(BaseModel):
    enabled: Optional[bool] = False


ProviderDeployResourceLimits = Annotated[
    Union[GCPDeployResourceLimits, AWSDeployResourceLimits],
    Field(discriminator="provider"),
]


class FrontendServiceSettings(BaseServiceSettings):
    type: Literal["frontend"]
    assets_path: Optional[str] = "build"
    build: List[str] = Field(default_factory=list)
    cors: Optional[CORSSettings] = None
    index_file_name: Optional[str] = "index.html"
    cdn: Optional[FrontendCDNConfig] = Field(default_factory=FrontendCDNConfig)

    @field_validator("build", mode="before")
    def validate_command(cls, value: Any) -> list[str]:
        return validate_command_list(value)

    @property
    def is_web(self):
        return True


class Worker(BaseModel):
    name: str
    command: List[str]
    system: Optional[ProviderDeployResourceLimits] = Field(
        default_factory=ProviderDeployResourceLimits,
    )
    replicas: Optional[int] = 1
    extended_duration: Optional[bool] = True

    settings: Optional[IgnoredType] = IgnoredType()

    # ------------------------------
    # Validators
    # ------------------------------

    @field_validator("command", mode="before")
    def validate_command(cls, value: Any) -> list[str]:
        return validate_command_list(value)

    @field_validator("name", mode="before")
    def validate_name(cls, value: str) -> str:
        return clean_name_string(value)

    @model_validator(mode="before")
    def ensure_system_provider(cls, data, info):
        if not data.get("system"):
            data["system"] = {}

        data["system"]["provider"] = info.context.get("provider")

        return data

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def is_ext_duration_enabled(self):
        return self.settings.service.environment.is_static and self.extended_duration

    @property
    def joined_command(self):
        return " ".join(self.command)

    # ------------------------------
    # Instance methods
    # ------------------------------

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} {self.name} "
            f"(service: {self.settings.service.name})>"
        )

    __str__ = __repr__


# TODO: discriminator for provider
class ScheduledTask(BaseModel):
    provider: str
    name: str
    command: List[str]
    raw_schedule: str = Field(alias="schedule")
    system: Optional[ProviderDeployResourceLimits] = Field(
        default_factory=ProviderDeployResourceLimits
    )

    # ------------------------------
    # Validators
    # ------------------------------
    @field_validator("command", mode="before")
    def validate_command(cls, value: Any) -> list[str]:
        return validate_command_list(value)

    @field_validator("name", mode="before")
    def validate_name(cls, value: str) -> str:
        return clean_name_string(value)

    @model_validator(mode="before")
    def ensure_system_provider(cls, data, info):
        if not data.get("system"):
            data["system"] = {}

        data["system"]["provider"] = info.context.get("provider")
        data["provider"] = info.context.get("provider")

        return data

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def schedule(self):
        if self.provider == "gcp":
            return self.raw_schedule
        elif self.provider == "aws":
            cron_exp = self.raw_schedule.split()
            # EventBridge expects an additional year component
            # on cron expressions
            cron_exp.append("*")
            # AWS EventBridge does not allow both day of month
            # and day of week to be specified one of them must be a "?"
            day_of_week = cron_exp[4]
            if day_of_week == "*":
                cron_exp[4] = "?"
            else:
                # day of month
                cron_exp[2] = "?"

            return " ".join(cron_exp)

    @property
    def joined_command(self):
        return " ".join(self.command)


class BackendServiceSettings(BaseServiceSettings):
    type: Literal["backend"]
    seed: List[str] = Field(default_factory=list)
    migrate: List[str] = Field(default_factory=list)
    workers: Optional[List[Worker]] = []
    scheduled_tasks: Optional[List[ScheduledTask]] = []
    cdn: Optional[BackendCDNConfig] = Field(default_factory=BackendCDNConfig)
    integrations: Optional[dict] = None

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="after")
    def annotate_children(self):
        for worker in self.workers:
            worker.settings = self

        return self

    @field_validator("seed", mode="before")
    def validate_seed(cls, value: Any) -> list[str]:
        return validate_command_list(value)

    @field_validator("migrate", mode="before")
    def validate_migrate(cls, value: Any) -> list[str]:
        return validate_command_list(value)

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def is_web(self):
        return True

    @property
    def target_group_name(self):
        if self.service.settings.system.health_check == "/":
            # Only append healthcheck hash
            # if default has been overwritten
            name = f"{self.service.instance_name[-32:].strip('-')}"
        else:
            _healthcheck_hash = hashlib.md5()
            _healthcheck_hash.update(
                (
                    self.service.instance_name
                    + self.service.settings.system.health_check
                ).encode()
            )
            healthcheck_hash = re.sub("\\W|_", "", _healthcheck_hash.hexdigest())
            name = healthcheck_hash[-32:]

        return re.sub("^-+", "", name)
