import re
import yaml
import traceback
import string
from typing import List, Optional
from pydantic import model_validator, ValidationInfo, field_validator, Field

from .base_model import BaseModel, IgnoredType
from .environment_variable import EnvironmentVariable
from .config import AppConfig
from .resource_use_existing import ResourceUseExistingSettings
from cnc.utils import clean_name_string

from cnc.logger import get_logger

log = get_logger(__name__)


class Environment(BaseModel):
    name: str
    # TODO: validate - no wildcard domains allowed here?
    custom_domains: Optional[List[str]] = []
    environment_variables: Optional[List[EnvironmentVariable]] = []
    config_file_path: Optional[str] = None
    config_data: Optional[dict] = {}
    image_tag: Optional[str] = "latest"
    # TODO: type should be set up for inclusion (static|preview|production)
    type: Optional[str] = "static"
    data: Optional[dict] = {}
    paused: Optional[bool] = False
    active_deployment: Optional[bool] = True
    database_password: Optional[EnvironmentVariable] = None
    provider: str
    raw_existing_resources: Optional[List[ResourceUseExistingSettings]] = Field(
        alias="existing_resources", default=[]
    )

    # ------------------------------
    # Parent relationships
    # (not meant to be set directly from configuration file)
    # ------------------------------
    config: Optional[IgnoredType] = IgnoredType()
    application: Optional[IgnoredType] = IgnoredType()
    collection: Optional[IgnoredType] = IgnoredType()

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="before")
    @classmethod
    def ensure_config_file_path_exists(cls, data: dict, info: ValidationInfo):
        """
        Sets default config_file_path if not set.
        See: Application.from_environments_yml for context
        """
        if not data.get("config_file_path"):
            data["config_file_path"] = info.context.get("config_file_path")
        return data

    @model_validator(mode="after")
    def ensure_config_data(self):
        """
        Loads config data from file if not already set
        """
        if not self.config_data:
            if self.config_file_path:
                with open(self.config_file_path) as coherence_yml_data:
                    self.config_data = yaml.safe_load(coherence_yml_data)
            else:
                log.debug("No config data and no config file path!")
                raise ValueError(f"No config data and no config file path for {self}!")

        self.config_data["environment"] = self

        try:
            self.config = AppConfig.model_validate(
                self.config_data, context={"provider": self.provider}
            )
        except Exception as e:
            log.warning(
                f"Cannot get AppConfig for environment! {traceback.format_exc()}"
            )
            raise e

        return self

    @model_validator(mode="after")
    def annotate_children(self):
        if self.config:
            for svc in self.config.services + self.config.settings.explicit_resources:
                svc.environment = self

        for variable in self.environment_variables:
            variable.environment = self

        if self.database_password:
            self.database_password.environment = self

        return self

    @field_validator("database_password", mode="before")
    def validate_database_password(cls, value: dict) -> dict:
        if value:
            value["name"] = "database_password"
        return value

    @field_validator("raw_existing_resources", mode="before")
    def validate_raw_existing_resources(cls, value: dict) -> list[dict]:
        return cls.convert_dict_keys_to_names(value)

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def is_static(self):
        return self.type in ["static", "production"]

    @property
    def is_production(self):
        return self.type == "production"

    @property
    def is_preview(self):
        return self.type == "preview"

    @property
    def services(self):
        if not hasattr(self, "_services"):
            self._services = []

        if not self._services and self.config:
            self._services += self.config.services
            self._services += self.config.settings.explicit_resources

        return self._services

    @property
    def web_services(self):
        return self.backend_services + self.frontend_services

    @property
    def backend_services(self):
        if not self.services:
            return []

        return [s for s in self.services if s.is_backend]

    @property
    def frontend_services(self):
        if not self.services:
            return []

        return [s for s in self.services if s.is_frontend]

    @property
    def active(self):
        return not self.paused

    @property
    def database_resources(self):
        return [s for s in self.services if s.is_database]

    @property
    def cache_resources(self):
        return [s for s in self.services if s.is_cache]

    @property
    def message_queue_resources(self):
        return [s for s in self.services if s.is_message_queue]

    @property
    def object_storage_resources(self):
        return [s for s in self.services if s.is_object_storage]

    @property
    def filesystem_resources(self):
        return [s for s in self.services if s.is_filesystem]

    @property
    def load_database_snapshot(self):
        return any(
            [db for db in self.database_resources if db.settings.snapshot_file_path]
        )

    @property
    def service_domains(self):
        domains = []
        for service in self.services:
            domains.append({"service_name": service.name, "domain": service.domain})
        return domains

    @property
    def domains(self):
        if self.collection.has_service_domains:
            return self.service_domains

        domains = [{"service_name": None, "domain": self.domain}]
        for domain in self.custom_domains:
            domains.append({"service_name": None, "domain": domain})

        return domains

    @property
    def domain(self):
        if not self.collection.has_service_domains:
            return f"{self.name}.{self.collection.base_domain}"

    @property
    def custom_ns_records(self):
        return self.data.get("custom_ns_records", {})

    @property
    def default_service(self):
        if self.frontend_services:
            return sorted(
                self.frontend_services,
                key=lambda x: len(x.settings.url_path),
            )[0]
        elif self.backend_services:
            return self.backend_services[0]

        return None

    @property
    def existing_resources(self):
        # order here is important so we return env-level first in the array!
        return self.raw_existing_resources + self.collection.existing_resources

    @property
    def instance_name(self):
        _name = (
            f"{self.collection.cloud_resource_namespace[:10]}-{self.application.name[-8:]}"
            f"-{self.collection.name[-9:]}-{self.name[-9:]}"
        )
        clean = clean_name_string(_name, truncate_len=39)

        if clean[0].lower() not in string.ascii_lowercase:
            clean = "c" + clean[1:]

        return re.sub("[\\W_]+$", "", clean)

    @property
    def managed_environment_items(self):
        return (
            self.config.managed_environment_variables
            + self.config.managed_environment_secrets
        )

    @property
    def environment_items(self):
        return self.environment_variables + self.managed_environment_items

    # ------------------------------
    # Instance methods
    # ------------------------------
    def __repr__(self):
        return (
            f"<Environment (name: {self.name} | collection: "
            f"{self.collection.name} | {[s.name for s in self.services]})>"
        )

    __str__ = __repr__

    def custom_ns_records_for(self, domain):
        return self.custom_ns_records.get(domain)

    def variable_by_name(self, name):
        for variable in self.environment_variables:
            if variable.name == name:
                return variable
        log.debug(f"{name} var not found for {self}")

    def service_by_name(self, name):
        for service in self.services:
            if service.name == name:
                return service
        log.debug(f"{name} service not found for {self}")
