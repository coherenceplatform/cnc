import re
import hashlib
import json
import string
from typing import List, Optional

from pydantic import model_validator, field_validator, Field

from .environment import Environment
from .base_model import BaseModel, IgnoredType
from .environment_variable import EnvironmentVariable
from .providers.amazon import AmazonAppServiceAccount
from .provisioner import ProvisionStageManager
from .resource_use_existing import ResourceUseExistingSettings
from cnc.utils import clean_name_string

from cnc.logger import get_logger

log = get_logger(__name__)


class IntegrationSettings(BaseModel):
    data: Optional[dict] = None


class EnvironmentCollection(BaseModel):
    name: str
    provided_base_domain: Optional[str] = Field(alias="base_domain", default=None)
    default: bool = False
    account_id: str
    environments: List[Environment]
    data: Optional[dict] = {}
    cloud_resource_namespace_override: Optional[str] = Field(
        alias="cloud_resource_namespace",
        default=None,
    )
    integrations: Optional[IntegrationSettings] = None
    database_password: Optional[EnvironmentVariable] = None
    existing_resources: Optional[List[ResourceUseExistingSettings]] = []
    collection_region: Optional[str] = Field(alias="region", default=None)

    # ------------------------------
    # Parent relationships
    # (not meant to be set directly from configuration file)
    # ------------------------------
    application: Optional[IgnoredType] = IgnoredType()

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="after")
    def annotate_children(self):
        for environment in self.environments:
            environment.collection = self

            for variable in environment.environment_variables:
                variable.collection = self

            if environment.database_password:
                environment.database_password.collection = self

        if self.database_password:
            self.database_password.collection = self

        return self

    @field_validator("existing_resources", mode="before")
    def validate_existing_resources(cls, value: dict) -> list[dict]:
        return cls.convert_dict_keys_to_names(value)

    @field_validator("cloud_resource_namespace_override", mode="before")
    def validate_cloud_resource_namespace(cls, value: str) -> str:
        assert value.startswith("c"), "cloud_resource_namespace must start with a c"

        return value[:11].replace("-", "")

    @field_validator("database_password", mode="before")
    def validate_database_password(cls, value: dict) -> dict:
        value["name"] = "database_password"
        return value

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def cloud_resource_namespace(self):
        return self.__class__.calculate_cloud_resource_namespace(
            self.account_id, self.application.name, self.name
        )

    @classmethod
    def calculate_cloud_resource_namespace(
        cls, account_id, application_name, collection_name
    ):
        _hash = hashlib.sha256()
        _hash.update(account_id.encode())
        _hash.update(application_name.encode())
        _hash.update(collection_name.encode())
        _hash = _hash.hexdigest()
        return f"c{_hash[:11]}"

    @property
    def instance_name(self):
        _name = (
            f"{self.cloud_resource_namespace[:12]}-{self.application.name[-12:]}"
            f"-{self.name[-13:]}"
        )
        clean = clean_name_string(_name, truncate_len=39)

        if clean[0].lower() not in string.ascii_lowercase:
            clean = "c" + clean[1:]

        return re.sub("[\\W_]+$", "", clean)

    @property
    def service_account(self):
        if self.application.provider_is_gcp:
            pass
            # return GoogleAppServiceAccount(collection=self)
        elif self.application.provider_is_aws:
            return AmazonAppServiceAccount(collection=self)

    @property
    def unique_id(self):
        _state = f"{self.cloud_resource_namespace}:{self.name}"

        for environment in self.environments:
            _state = _state + environment.name

            _data = environment.config_data.copy()
            del _data["environment"]

            _state = _state + json.dumps(_data, sort_keys=True)

        _hash = hashlib.sha256()
        _hash.update(_state.encode())
        _unique_id = _hash.hexdigest()

        return _unique_id

    @property
    def config_files_path(self):
        return f"{self.application.config_files_path}/{self.unique_id}"

    @property
    def valid_environments(self):
        "Includes all valid environments (active + paused)"
        return [e for e in self.environments if e.config]

    @property
    def active_environments(self):
        "Valid active environments"
        return [e for e in self.valid_environments if e.active]

    @property
    def has_active_deployments(self):
        return any([e for e in self.active_environments if e.active_deployment])

    @property
    def paused_environments(self):
        "Valid paused environments"
        return [e for e in self.valid_environments if e.paused]

    @property
    def environments_with_databases(self):
        environments = []
        for environment in self.valid_environments:
            if environment.database_resources:
                environments.append(environment)
        return environments

    @property
    def backend_services(self):
        "non-unique, used in infra to provision several envs"
        return self.all_services_for_type("backend")

    @property
    def frontend_services(self):
        "non-unique, used in infra to provision several envs"
        return self.all_services_for_type("frontend")

    @property
    def all_services(self):
        return self.all_services_for_type()

    @property
    def all_web_services(self):
        return self.all_services_for_type(["frontend", "backend"])

    @property
    def database_resources(self):
        return self.all_services_for_type("database")

    @property
    def cache_resources(self):
        return self.all_services_for_type("cache")

    @property
    def object_storage_resources(self):
        return self.all_services_for_type("object_storage")

    @property
    def message_queue_resources(self):
        return self.all_services_for_type("message_queue")

    @property
    def has_object_storage(self):
        return bool(self.object_storage_resources)

    @property
    def has_message_queues(self):
        return bool(self.message_queue_resources)

    @property
    def load_database_snapshot(self):
        return any([e for e in self.environments if e.load_database_snapshot])

    @property
    def default_service(self):
        for service in self.frontend_services + self.backend_services:
            if service.environment.active_deployment:
                return service

    @property
    def has_service_domains(self):
        return False

    @property
    def base_domain(self):
        if self.provided_base_domain:
            return self.provided_base_domain

    @property
    def domains(self):
        domains = []
        for environment in self.environments:
            domains.extend(environment.domains)
        return sorted(domains, key=lambda x: x.get("domain"))

    @property
    def domain_buckets(self):
        buckets = {}

        for domain_info in self.domains:
            domain = domain_info.get("domain", "")
            # 6 buckets = approx. 70 domains on gcp
            bucket = int((hashlib.sha256(domain.encode()).hexdigest()), 16) % 6

            if bucket not in buckets:
                buckets[bucket] = []

            buckets[bucket].append(domain)

        return buckets

    @property
    def needs_k8s(self):
        if self.application.flavor == "gke":
            return True

        for service in self.all_services_for_type():
            if service.is_backend and (
                service.settings.workers or service.settings.scheduled_tasks
            ):
                return True

    @property
    def provision_stage_manager(self):
        if not hasattr(self, "_provision_stage_manager"):
            self._provision_stage_manager = ProvisionStageManager(self)
        return self._provision_stage_manager

    @property
    def region(self):
        return self.collection_region or self.application.region

    @property
    def includes_production(self):
        return any([e for e in self.environments if e.is_production])

    # ------------------------------
    # Instance methods
    # ------------------------------
    def __repr__(self):
        return (
            f"<EnvironmentCollection ({self.name} | "
            f"{self.account_id}) [{len(self.environments)} envs]>"
        )

    __str__ = __repr__

    def all_services_for_type(self, service_type=None):
        "non-unique, returns all active services by service_type"
        _all = []
        for environment in self.active_environments:
            for service in environment.services:
                if service_type:
                    if isinstance(service_type, list):
                        if service.settings.type not in service_type:
                            continue
                    elif service.settings.type != service_type:
                        continue

                _all.append(service)

        return sorted(_all, key=lambda x: x.settings.unique_id)

    def infra_outputs(self, force_cache_refresh=False):
        _config = None

        if "infrastructure_outputs" not in self.data:
            try:
                if (not hasattr(self, "_infra_outputs_cache")) or force_cache_refresh:
                    log.debug(f"Going to get outputs for {self}: {self.data}")
                    _config = ProvisionStageManager(
                        self,
                        output_only=True,
                    )
                    _config.make_ready_for_use()
                    self._infra_outputs_cache = _config.output()
            except Exception as e:
                log.debug(f"Cannot get TF outputs for {self}: {e}")
                if not hasattr(self, "_infra_outputs_cache"):
                    self._infra_outputs_cache = {}
            finally:
                if _config:
                    _config.cleanup()
        else:
            self._infra_outputs_cache = {}

        infra_outputs = {}
        infra_outputs.update(self.data.get("infrastructure_outputs", {}))
        infra_outputs.update(self._infra_outputs_cache)

        return infra_outputs

    def get_terraform_output(self, output_name, force_cache_refresh=False):
        return (
            self.infra_outputs(force_cache_refresh=force_cache_refresh)
            .get(output_name, {})
            .get("value", "")
        )

    def generate_tf_assets(self, *args, **kwargs):
        return True

    def environment_by_name(self, environment_name):
        for environment in self.environments:
            if environment.name == environment_name:
                return environment
