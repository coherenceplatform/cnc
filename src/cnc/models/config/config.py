import re
import hashlib
from typing import List, Optional, Union, Any

from pydantic import BaseModel, field_validator, Field, model_validator

from cnc.constants import EnvironmentVariableTypes

# from cnc.constants import EnvironmentVariableDestinations
from ..environment_variable import EnvironmentVariable
from .resource import (
    CacheResourceSettings,
    QueueResourceSettings,
    BucketResourceSettings,
)
from .service import Service, ProviderDatabaseResourceSettings

from cnc.logger import get_logger

log = get_logger(__name__)


class PlatformBuildSettings(BaseModel):
    machine_type: str


class BuildSettings(BaseModel):
    platform_settings: Optional[PlatformBuildSettings] = {}


class ResourceService(Service):
    settings: Union[
        ProviderDatabaseResourceSettings,
        CacheResourceSettings,
        BucketResourceSettings,
        QueueResourceSettings,
    ] = Field(alias="x-cnc", discriminator="type")


class InternalSettings(BaseModel):
    build_settings: Optional[BuildSettings] = {}
    preview_inactivity_timeout_hours: Optional[int] = 90 * 24
    explicit_resources: Optional[List[ResourceService]] = Field(
        default_factory=list,
        alias="resources",
    )

    @field_validator("explicit_resources", mode="before")
    def format_resources(cls, value: list):
        formatted_resource_svcs = []
        for resource in value:
            resource_name = resource["name"]
            del resource["name"]

            formatted_resource_svcs.append(
                {
                    "name": resource_name,
                    "x-cnc": resource,
                }
            )

        return formatted_resource_svcs


class AppConfig(BaseModel):
    settings: Optional[InternalSettings] = Field(
        default_factory=InternalSettings, alias="x-cnc"
    )
    services: List[Service]

    # ------------------------------
    # Parent relationships
    # ------------------------------
    environment: Optional[Any] = None

    def __repr__(self):
        return f"<AppConfig: {[s.name for s in self.services]}>"

    __str__ = __repr__

    @field_validator("services", mode="before")
    def validate_services(cls, value: dict) -> list[dict]:
        with_names = []
        for k, v in value.items():
            if not isinstance(v, dict):
                raise ValueError(
                    f"({k} is bad compose service - service values must be dictionaries!"
                )

            # this is to ensure we ignore config from the compose file
            v.update({"name": k})
            if v.get("config"):
                del v["config"]

            with_names.append(v)
        return with_names

    @model_validator(mode="after")
    def annotate_children(self):
        for service in self.services + self.settings.explicit_resources:
            service.config = self
            service.settings.config = self

        return self

    @property
    def resources(self):
        all_resources = []

        for service in self.services:
            if service.settings.type in ["database", "cache"]:
                all_resources.append(service)

        all_resources.extend(self.settings.explicit_resources)

        return all_resources

    @property
    def unique_id(self):
        hash_strings = []

        for service in self.services:
            hash_strings.append(service.settings.unique_id)

        _hash = hashlib.sha256()
        _hash.update(":".join(sorted(hash_strings)).encode())
        return _hash.hexdigest()

    @property
    def has_backend(self):
        return any(s.is_backend for s in self.services)

    def filtered_environment_items(
        self, service_name=None, variable_type=None, pattern=None
    ):
        if (
            variable_type
            and variable_type not in EnvironmentVariableTypes.allowed_types()
        ):
            raise ValueError(
                f"Invalid variable type in filtered_environment_items: {variable_type}"
            )

        regex_vars_by_name = []
        for item in self.environment.environment_variables:
            if pattern:
                if re.match(pattern, item.name):
                    regex_vars_by_name.append(item)
            else:
                regex_vars_by_name.append(item)

        service_vars = []
        for env_item in regex_vars_by_name:
            if not service_name:
                service_vars.append(env_item)
            elif (not env_item.service) or (env_item.service == service_name):
                service_vars.append(env_item)

        type_vars = []
        if variable_type:
            for item in service_vars:
                if variable_type == item.variable_type:
                    type_vars.append(item)
                elif (
                    variable_type == EnvironmentVariableTypes.VARIABLE_TYPE_SECRET
                    and item.alias
                    and item.secret_id
                ):
                    type_vars.append(item)
                elif (
                    variable_type == EnvironmentVariableTypes.VARIABLE_TYPE_OUTPUT
                    and item.alias
                    and item.output_name
                ):
                    type_vars.append(item)
                elif (
                    variable_type == EnvironmentVariableTypes.VARIABLE_TYPE_STANDARD
                    and item.alias
                    and not item.output_name
                    and not item.secret_id
                ):
                    type_vars.append(item)
        else:
            type_vars = service_vars

        return type_vars

    @property
    def reserved_environment_item_names(self):
        all_names = []

        for item in self.managed_environment_variables:
            all_names.append(item.name)
        for item in self.managed_environment_secrets:
            all_names.append(item.name)

        return set(all_names)

    @property
    def managed_environment_variables(self):
        return self.managed_environment_variables_for_service()

    @property
    def managed_environment_secrets(self):
        return self.managed_environment_secrets_for_service()

    def managed_environment_variables_for_service(self, service=None):
        _vars = {
            "CNC_APPLICATION_NAME": self.environment.application.name,
            "CNC_ENVIRONMENT_NAME": self.environment.name,
            "CNC_ENVIRONMENT_DOMAIN": (
                self.environment.domains[0]["domain"]
                if self.environment.domains
                else ""
            ),
            "CNC_ENVIRONMENT_CUSTOM_DOMAIN": (
                self.environment.custom_domains[0]
                if self.environment.custom_domains
                else ""
            ),
            "CNC_ENVIRONMENT_REGION": self.environment.collection.region,
        }

        sorted_services = sorted(self.services, key=lambda s: s == service)
        for service in sorted_services:
            _vars.update(service.settings.managed_environment_variables)

        variable_objects = []
        for k, v in _vars.items():
            if v:
                variable_objects.append(self.variable_object({"name": k, "value": v}))

        return variable_objects

    def managed_environment_secrets_for_service(self, service=None):
        _vars = {}

        sorted_resources = sorted(self.resources, key=lambda s: s == service)
        for resource in sorted_resources:
            _vars.update(resource.settings.managed_environment_secrets)

        return [
            self.variable_object({"name": k, "secret_id": v}) for k, v in _vars.items()
        ]

    @property
    def database_resources(self):
        instances = []

        for resource in self.resources:
            if resource.is_database:
                instances.append(resource)

        return instances

    @property
    def cache_resources(self):
        instances = []

        for resource in self.resources:
            if resource.is_cache:
                instances.append(resource)

        return instances

    @property
    def object_storage_resources(self):
        instances = []

        for resource in self.resources:
            if resource.is_object_storage:
                instances.append(resource)

        return instances

    def variable_object(self, data):
        variable = EnvironmentVariable.model_validate(data)
        variable.environment = self.environment
        variable.collection = self.environment.collection
        return variable
